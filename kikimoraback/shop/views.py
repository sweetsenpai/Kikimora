from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib import messages
from django.template import loader
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.urls import reverse
from django.db.models import Q
from .models import CustomUser
from .forms import AdminCreationForm


class AdminHomePageView(TemplateView):
    template_name = 'master/home.html'


def apanel_staff(request):
    if request.method == "POST":
        email = request.POST.get('email')
        fio = request.POST.get('fio')
        phone = request.POST.get('phone')
        search_result = {'admins':  CustomUser.objects.filter(Q(email=email) | Q(phone=phone) |Q(user_fio=fio), is_staff=True)}
        return render(request, template_name='master/staff.html', context=search_result)
    admins = {'admins': CustomUser.objects.all().filter(is_staff=True).order_by('user_id').values()}
    return render(request, template_name='master/staff.html', context=admins)


def admin_account(request, admin_id):
    if request.method=="POST":
        ...
    print(request)
    admin_data = {'admin': CustomUser.objects.all().filter(user_id=admin_id).values()}
    return render(request, template_name='master/admin_page.html', context=admin_data)


def addadmin(request):
    if request.method == 'POST':
        form = AdminCreationForm(request.POST)
        print(form.data)
        if form.is_valid():
            form.save()
            return redirect('/staff')
        else:
            print('ERROR!!!!!!!!!!!!!!!')
    form = AdminCreationForm(initial={'is_staff': True})
    return render(request, 'master/test.html', {'form': form})
