import json
import logging
from abc import ABC
from datetime import datetime

from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import LoginView
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import OuterRef, Prefetch, Q, Subquery
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.views.generic import DeleteView, FormView, ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView, View

from celery.result import AsyncResult

from shop_api.tasks import *

from ..forms import *
from ..models import *

logger = logging.getLogger("shop")
logger.setLevel(logging.DEBUG)


def is_staff_or_superuser(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


class StaffCheckRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return is_staff_or_superuser(self.request.user)

    def handle_no_permission(self):
        return redirect("admin_login")


class AdminProdactListView(StaffCheckRequiredMixin, ListView):
    model = Product
    template_name = "master/product/products.html"
    context_object_name = "products"

    def get_queryset(self):
        self.subcategory = get_object_or_404(Subcategory, pk=self.kwargs["subcategory_id"])
        photos_prefetch = Prefetch(
            "photos",
            queryset=ProductPhoto.objects.order_by("-is_main", "photo_id"),
            to_attr="prefetched_photos",
        )
        queryset = (
            Product.objects.filter(subcategory=self.subcategory)
            .prefetch_related(photos_prefetch)
            .order_by("product_id")
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["subcategory"] = self.subcategory
        return context

    def post(self, request, **kwargs):
        subcategory_id = self.kwargs.get("subcategory_id")
        self.subcategory = get_object_or_404(Subcategory, pk=subcategory_id)

        name = request.POST.get("name")
        if not name:
            products = Product.objects.filter(subcategory=self.subcategory).order_by("product_id")
        else:
            products = Product.objects.filter(name=name).order_by("product_id")

        context = {"products": products, "subcategory": self.subcategory}

        return render(request, self.template_name, context)


@user_passes_test(is_staff_or_superuser)
def toggle_visibility_product(request, product_id):
    if request.method == "POST":
        product = get_object_or_404(Product, pk=product_id)
        product.visibility = not product.visibility
        product.save()
        return JsonResponse({"visibility": product.visibility})
    return JsonResponse({"error": "Invalid request"}, status=400)


class ProductUpdateView(StaffCheckRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = "master/product/product_form.html"
    context_object_name = "product"

    def get_object(self, queryset=None):
        return Product.objects.get(product_id=self.kwargs.get("product_id"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.get_object()
        context["first_photo"] = product.photos.first()
        context["tags"] = ProductTag.objects.all()
        return context

    def form_valid(self, form):
        product = self.get_object()
        for field in form.cleaned_data:
            new_value = form.cleaned_data.get(field)
            if new_value:
                setattr(product, field, new_value)
        product.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("product_update", kwargs={"product_id": self.object.product_id})


class AdminTagView(StaffCheckRequiredMixin, ListView):
    template_name = "master/tag/tags.html"
    context_object_name = "tags"
    queryset = ProductTag.objects.all()


class AdminNewTag(StaffCheckRequiredMixin, CreateView):
    template_name = "master/tag/new_tag.html"
    form_class = TagForm
    success_url = reverse_lazy("tags")


class AdminDeleteTag(StaffCheckRequiredMixin, DeleteView):
    model = ProductTag
    success_url = reverse_lazy("tags")
    slug_field = "tag_id"
    slug_url_kwarg = "tag_id"


class AdminDiscountListView(StaffCheckRequiredMixin, ListView):
    model = Discount
    template_name = "master/discount/discounts.html"
    context_object_name = "discounts"

    def get_queryset(self):
        return Discount.objects.all().order_by("-discount_id")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["current_time"] = timezone.now()
        return context


# TODO вынести логику id в модель
class AdminNewDiscount(StaffCheckRequiredMixin, FormView):
    form_class = DiscountForm
    template_name = "master/discount/new_discount.html"
    success_url = reverse_lazy("discounts")

    def form_valid(self, form):
        if form.instance.start.date() == datetime.now():
            form.instance.active = True
            discount = form.save()
            discount.task_id_end = deactivate_expired_discount.apply_async(
                (discount.discount_id,), eta=discount.end
            )
        else:
            form.instance.active = False
            discount = form.save()
            discount.task_id_start = activate_discount.apply_async(
                (discount.discount_id,), eta=discount.start
            )
            discount.task_id_end = deactivate_expired_discount.apply_async(
                (discount.discount_id,), eta=discount.end
            )
        discount.save()
        return super().form_valid(form)


@user_passes_test(is_staff_or_superuser)
def delete_discount(request, discount_id):
    template_name = "master/discount/old_discount.html"
    discount = get_object_or_404(Discount, pk=discount_id)
    if request.method == "POST":
        discount.delete()
        return JsonResponse({"status": "success"})
    return render(request, template_name=template_name, context={"discount": discount})


class AdminPromocodeListView(StaffCheckRequiredMixin, ListView):
    model = PromoSystem
    template_name = "master/promo/promocods.html"
    context_object_name = "promocodes"

    def get_queryset(self):
        return PromoSystem.objects.all().order_by("-promo_id")


# TODO вынести логику работы с тасками в модель
class AdminNewPromo(StaffCheckRequiredMixin, FormView):
    template_name = "master/promo/new_promocode.html"
    success_url = reverse_lazy("promocods")
    form_class = PromocodeForm

    def form_valid(self, form):
        if form.instance.start.date() == datetime.now():
            form.instance.active = True
            promo = form.save()
            promo.task_id_end = deactivate_expired_promo.apply_async(
                (promo.promo_id,), eta=promo.end
            )
        else:
            form.instance.active = False
            promo = form.save()
            promo.task_id_start = activate_promo.apply_async((promo.promo_id,), eta=promo.start)
            promo.task_id_end = deactivate_expired_promo.apply_async(
                (promo.promo_id,), eta=promo.end
            )
        promo.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)


@user_passes_test(is_staff_or_superuser)
def delete_promo(request, promo_id):
    template_name = "master/promo/old_promo.html"
    promo = get_object_or_404(PromoSystem, pk=promo_id)
    if request.method == "POST":
        promo.delete()
        return redirect("promocods")
    return render(request, template_name=template_name, context={"promo": promo})


class AdminLimitTimeProduct(StaffCheckRequiredMixin, ListView):
    template_name = "master/product/limit_time_products.html"
    context_object_name = "limit_products"
    model = LimitTimeProduct

    def get_queryset(self):
        return LimitTimeProduct.objects.all().order_by("-limittimeproduct_id")


# TODO вынести логику работы с task в модель
# TODO тестим ниже
class AdminLimitTimeProductForm(StaffCheckRequiredMixin, FormView):
    template_name = "master/product/limit_time_product_form.html"
    form_class = LimiteTimeProductForm
    success_url = reverse_lazy("day_products")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = self.kwargs["product_id"]
        product = Product.objects.get(product_id=product_id)  # Получаем товар

        # Добавляем товар в контекст
        context["product"] = product
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        product_id = self.kwargs["product_id"]
        product = Product.objects.get(product_id=product_id)

        # Передаем данные о товаре в форму, если нужно
        kwargs["initial"] = {
            "product_id": product.product_id,
        }
        return kwargs

    def form_valid(self, form):
        form.instance.product_id = Product.objects.get(product_id=self.kwargs["product_id"])
        limit_time_product = form.save()
        due_time = limit_time_product.due
        task = delete_limite_time_product.apply_async(
            (limit_time_product.limittimeproduct_id,), eta=due_time
        )
        limit_time_product.task_id = task.id
        limit_time_product.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)
