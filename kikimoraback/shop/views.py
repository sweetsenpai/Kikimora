from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView, FormView
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse, reverse_lazy
from django.db.models import Q
from .models import *
from .forms import *
from django.utils.crypto import get_random_string
from .tasks import new_admin_mail


class AdminHomePageView(TemplateView):
    template_name = 'master/home.html'


class StaffListView(ListView):
    template_name = 'master/staff.html'
    context_object_name = 'admins'

    def get_queryset(self):
        return CustomUser.objects.filter(is_staff=True).order_by('user_id').values()

    def post(self, request, *args, **kwargs):
        email = request.POST.get('email')
        fio = request.POST.get('fio')
        phone = request.POST.get('phone')
        search_query = Q(email=email) | Q(phone=phone) | Q(user_fio=fio)
        self.object_list = CustomUser.objects.filter(search_query, is_staff=True)
        return self.render_to_response(self.get_context_data(object_list=self.object_list))


class AdminCreateView(FormView):
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
        # TODO uncoment code below
        # new_admin_mail.delay(password, new_user.email)
        return JsonResponse({'status': 'success', 'redirect_url': self.success_url})

    def form_invalid(self, form):
        errors = {field: error_list[0] for field, error_list in form.errors.items()}
        return JsonResponse({'status': 'error', 'errors': errors})


def admin_account(request, admin_id):
    if request.method=="POST":

        ex_admin = get_object_or_404(CustomUser, user_id=admin_id)
        ex_admin.is_staff = False
        ex_admin.is_superuser = False
        ex_admin.save()
        return JsonResponse({'status': 'success', 'redirect_url': '/staff'})

    admin_data = {'admin': CustomUser.objects.get(user_id=admin_id)}
    return render(request, template_name='master/admin_page.html', context=admin_data)


class AdminCategoryView(ListView):
    template_name = 'master/category.html'
    context_object_name = 'categories'
    form_class = CategoryCreationForm

    def get_queryset(self):
        return Category.objects.all().order_by('category_id')

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_category_view')
        else:
            print(form.errors)
            return render(request, template_name=self.template_name, context={'categories': self.get_queryset(), 'form': form})
