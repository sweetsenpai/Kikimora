from abc import ABC

from django.shortcuts import render, redirect, get_object_or_404

from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.views import LoginView

from django.views.generic import ListView, TemplateView, FormView
from django.views.generic.edit import CreateView, UpdateView

from django.utils import timezone


from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseBadRequest

from django.urls import reverse, reverse_lazy
from django.db.models import Q

from django.core.cache import cache

from ..models import *
from ..forms import *
from ..tasks import new_admin_mail, delete_limite_time_product, deactivate_expired_discount, deactivate_expired_promo, activate_promo, activate_discount

from celery.result import AsyncResult


def is_staff_or_superuser(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


class StaffCheckRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (self.request.user.is_superuser or self.request.user.is_staff)

    def handle_no_permission(self):
        return redirect('admin_login')


class AdminLogin(LoginView):
    template_name='master/login.html'
    redirect_authenticated_user = True

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me', False)

        user = authenticate(request, username=email, password=password)
        if user is not None:
            # Проверяем, является ли пользователь сотрудником или суперпользователем
            if user.is_staff or user.is_superuser:
                login(request, user)
                if not remember_me:
                    # Устанавливаем сессию на один день
                    request.session.set_expiry(0)
                return HttpResponseRedirect(reverse_lazy('admin_home'))
            else:
                messages.error(request, "У вас нет доступа к административной панели.")
        else:
            messages.error(request, "Неправильный email или пароль.")
        return render(request, self.template_name)


class AdminHomePageView(StaffCheckRequiredMixin, TemplateView):
    template_name = 'master/home.html'


class StaffListView(StaffCheckRequiredMixin, ListView):
    template_name = 'master/staff.html'
    context_object_name = 'admins'

    def get_queryset(self):
        cache_key = 'staff_list'
        staff_list = cache.get(cache_key)
        if not staff_list:
            staff_list = CustomUser.objects.filter(is_staff=True).order_by('user_id').values()
            cache.set(cache_key, staff_list, timeout=60*15)
        return staff_list

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        fio = request.POST.get('fio')
        phone = request.POST.get('phone')
        search_query = Q(email=email) | Q(phone=phone) | Q(user_fio=fio)
        self.object_list = CustomUser.objects.filter(search_query, is_staff=True)
        return self.render_to_response(self.get_context_data(object_list=self.object_list))


class AdminCreateView(StaffCheckRequiredMixin, FormView):
    template_name = 'master/admin_creation_page.html'
    form_class = AdminCreationForm
    success_url = reverse_lazy('staff')

    def form_valid(self, form):
        user_fio = form.cleaned_data['user_fio']
        email = form.cleaned_data['email']
        phone = form.cleaned_data['phone']
        is_superuser = form.cleaned_data['is_superuser']
        new_user = CustomUser(user_fio=user_fio, email=email,
                              phone=phone, is_superuser=is_superuser,
                              is_staff=True)
        password = get_random_string(20)
        new_user.set_password(password)
        new_user.save()
        new_admin_mail.delay(password, new_user.email)
        return JsonResponse({'status': 'success', 'redirect_url': self.success_url})

    def form_invalid(self, form):
        errors = {field: error_list[0] for field, error_list in form.errors.items()}
        return JsonResponse({'status': 'error', 'errors': errors})


@user_passes_test(is_staff_or_superuser)
def admin_account(request, admin_id):
    if request.method=="POST":

        ex_admin = get_object_or_404(CustomUser, user_id=admin_id)
        ex_admin.is_staff = False
        ex_admin.is_superuser = False
        ex_admin.save()
        return JsonResponse({'status': 'success', 'redirect_url': '/staff'})

    admin_data = {'admin': CustomUser.objects.get(user_id=admin_id)}
    return render(request, template_name='master/admin_page.html', context=admin_data)


class AdminCategoryView(StaffCheckRequiredMixin, ListView):
    template_name = 'master/category.html'
    context_object_name = 'categories'
    form_class = CategoryCreationForm

    def get_queryset(self):
        cache_key = 'categories_list'
        categories_list = cache.get(cache_key)
        if not categories_list:
            categories_list = Category.objects.all().order_by('category_id')
            cache.set(cache_key, categories_list, timeout=60*15)
        return categories_list


@user_passes_test(is_staff_or_superuser)
def toggle_visibility_category(request, category_id):
    if request.method == 'POST':
        category = get_object_or_404(Category, pk=category_id)
        category.visibility = not category.visibility
        category.save()
        cache.delete('categories_list')
        return JsonResponse({'visibility': category.visibility})
    return JsonResponse({'error': 'Invalid request'}, status=400)


class AdminSubcategoryListView(StaffCheckRequiredMixin, ListView):
    model = Subcategory
    template_name = 'master/subcategory.html'
    context_object_name = 'subcategories'

    def get_queryset(self):
        self.category = get_object_or_404(Category, pk=self.kwargs['category_id'])
        return Subcategory.objects.filter(category=self.category).order_by('subcategory_id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        return context


@user_passes_test(is_staff_or_superuser)
def toggle_visibility_subcat(request, subcategory_id):
    if request.method == 'POST':
        subcategory = get_object_or_404(Subcategory, pk=subcategory_id)
        subcategory.visibility = not subcategory.visibility
        subcategory.save()
        return JsonResponse({'visibility': subcategory.visibility})
    return JsonResponse({'error': 'Invalid request'}, status=400)


class AdminProdactListView(StaffCheckRequiredMixin, ListView):
    model = Product
    template_name = 'master/products.html'
    context_object_name = 'products'

    def get_queryset(self):
        self.subcategory = get_object_or_404(Subcategory, pk=self.kwargs['subcategory_id'])
        return Product.objects.filter(subcategory=self.subcategory).order_by('product_id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['subcategory'] = self.subcategory
        return context

    def post(self, request, **kwargs):
        subcategory_id = self.kwargs.get('subcategory_id')
        self.subcategory = get_object_or_404(Subcategory, pk=subcategory_id)

        name = request.POST.get('name')
        if not name:
            products = Product.objects.filter(subcategory=self.subcategory).order_by('product_id')
        else:
            products = Product.objects.filter(name=name).order_by('product_id')

        context = {
            'products': products,
            'subcategory': self.subcategory
        }

        return render(request, self.template_name, context)


@user_passes_test(is_staff_or_superuser)
def toggle_visibility_product(request, product_id):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=product_id)
        product.visibility = not product.visibility
        product.save()
        return JsonResponse({'visibility': product.visibility})
    return JsonResponse({'error': 'Invalid request'}, status=400)


class ProductUpdateView(StaffCheckRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'master/product_form.html'
    context_object_name = 'product'

    def get_object(self, queryset=None):
        return Product.objects.get(product_id=self.kwargs.get('product_id'))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = Product.objects.get(product_id=self.kwargs.get('product_id'))
        context['category_id'] = product.subcategory.category.category_id
        context['subcategory_id'] = product.subcategory.subcategory_id
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
        return reverse('product_update', kwargs={'product_id': self.object.product_id})


class AdminDiscountListView(StaffCheckRequiredMixin, ListView):
    model = Discount
    template_name = 'master/discounts.html'
    context_object_name = 'discounts'

    def get_queryset(self):
        return Discount.objects.all().order_by('-discount_id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_time'] = timezone.now()
        return context


class AdminNewDiscount(StaffCheckRequiredMixin, FormView):
    form_class = DiscountForm
    template_name = 'master/new_discount.html'
    success_url = reverse_lazy('discounts')

    def form_valid(self, form):
        if form.instance.start.date() == datetime.now():
            form.instance.active = True
            discount = form.save()
            discount.task_id_end = deactivate_expired_discount.apply_async((discount.discount_id,), eta=discount.end)
        else:
            form.instance.active = False
            discount = form.save()
            discount.task_id_start = activate_discount.apply_async((discount.discount_id,), eta=discount.start)
            discount.task_id_end = deactivate_expired_discount.apply_async((discount.discount_id,), eta=discount.end)
        discount.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)


@user_passes_test(is_staff_or_superuser)
def delete_discount(request, discount_id):
    template_name = 'master/old_discount.html'
    discount = get_object_or_404(Discount, pk=discount_id)
    if request.method == 'POST':
        discount.delete()
        return JsonResponse({'status': 'success'})
    return render(request, template_name=template_name, context={'discount': discount})


class AdminPromocodeListView(StaffCheckRequiredMixin, ListView):
    model = PromoSystem
    template_name = 'master/promocods.html'
    context_object_name = 'promocodes'

    def get_queryset(self):
        return PromoSystem.objects.all().order_by('-promo_id')


class AdminNewPromo(StaffCheckRequiredMixin, FormView):
    template_name = 'master/new_promocode.html'
    success_url = reverse_lazy('promocods')
    form_class = PromocodeForm

    def form_valid(self, form):
        if form.instance.start.date() == datetime.now():
            form.instance.active = True
            promo = form.save()
            promo.task_id_end = deactivate_expired_promo.apply_async((promo.promo_id,), eta=promo.end)
        else:
            form.instance.active = False
            promo = form.save()
            promo.task_id_start = activate_promo.apply_async((promo.promo_id,), eta=promo.start)
            promo.task_id_end = deactivate_expired_promo.apply_async((promo.promo_id,), eta=promo.end)
        promo.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)


@user_passes_test(is_staff_or_superuser)
def delete_promo(request, promo_id):
    template_name = 'master/old_promo.html'
    promo = get_object_or_404(PromoSystem, pk=promo_id)
    if request.method == 'POST':
        if promo.task_id_start:
            AsyncResult(id=promo.task_id_start).revoke(terminate=True)
        AsyncResult(id=promo.task_id_end).revoke(terminate=True)
        promo.delete()
        return redirect('promocods')
    return render(request, template_name=template_name, context={'promo': promo})


class AdminLimitTimeProduct(StaffCheckRequiredMixin, ListView):
    template_name = 'master/limit_time_products.html'
    context_object_name = 'limit_products'
    model = LimitTimeProduct

    def get_queryset(self):
        return LimitTimeProduct.objects.all().order_by('-limittimeproduct_id')


class AdminLimitTimeProductForm(StaffCheckRequiredMixin, FormView):
    template_name = 'master/limit_time_product_form.html'
    form_class = LimiteTimeProductForm
    success_url = reverse_lazy('day_products')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product_id = self.kwargs['product_id']
        product = Product.objects.get(product_id=product_id)  # Получаем товар

        # Добавляем товар в контекст
        context['product'] = product
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        product_id = self.kwargs['product_id']
        product = Product.objects.get(product_id=product_id)

        # Передаем данные о товаре в форму, если нужно
        kwargs['initial'] = {
            'product_id': product.product_id,
        }
        return kwargs

    def form_valid(self, form):
        form.instance.product_id = Product.objects.get(product_id=self.kwargs['product_id'])
        limit_time_product = form.save()
        due_time = limit_time_product.due
        task = delete_limite_time_product.apply_async((limit_time_product.limittimeproduct_id,), eta=due_time)
        limit_time_product.task_id = task.id
        limit_time_product.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        return super().form_invalid(form)