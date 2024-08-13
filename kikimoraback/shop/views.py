from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse
from django.db.models import Q
from .models import CustomUser
from .forms import AdminCreationForm
from django.utils.crypto import get_random_string
from .email_sending import new_admin_mail


class AdminHomePageView(TemplateView):
    template_name = 'master/home.html'


def apanel_staff(request):
    if request.method == "POST":
        email = request.POST.get('email')
        fio = request.POST.get('fio')
        phone = request.POST.get('phone')
        search_query = Q(email=email) | Q(phone=phone) | Q(user_fio=fio)
        search_result = {'admins':  CustomUser.objects.filter(search_query, is_staff=True)}
        return render(request, template_name='master/staff.html', context=search_result)
    admins = {'admins': CustomUser.objects.all().filter(is_staff=True).order_by('user_id').values()}
    return render(request, template_name='master/staff.html', context=admins)


def addadmin(request):
    if request.method == 'POST':
        form = AdminCreationForm(request.POST)
        if form.is_valid():
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
            new_admin_mail(password, new_user.email)
            return JsonResponse({'status': 'success', 'redirect_url': '/staff'})
        else:
            return render(request, 'master/admin_creation_page.html', {'form': form})
    form = AdminCreationForm()
    return render(request, 'master/admin_creation_page.html', {'form': form})


def admin_account(request, admin_id):
    if request.method=="POST":
        ex_admin = CustomUser.objects.get_object_or_404(user_id=admin_id)
        ex_admin.is_staff = False
        ex_admin.is_superuser = False
        ex_admin.save()
        return JsonResponse({'status': 'success', 'redirect_url': '/staff'})
    admin_data = {'admin': CustomUser.objects.all().filter(user_id=admin_id).values()}
    return render(request, template_name='master/admin_page.html', context=admin_data)