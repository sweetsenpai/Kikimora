from django.contrib.auth import login, get_user_model
from django.contrib.auth.views import LoginView
from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView, ListView
from django_filters.views import FilterView
from shop.forms import AdminLoginForm
from shop.mixins import StaffCheckRequiredMixin
from shop.filters import StaffFilter


class AdminLogin(LoginView):
    """
    Представление для входа администратора в систему.

    Использует кастомную форму аутентификации AdminLoginForm и шаблон master/login.html.
    При успешной аутентификации выполняет вход пользователя с учетом опции "запомнить меня":
    если пользователь не выбрал запомнить, сессия истекает при закрытии браузера.
    Перенаправляет аутентифицированного пользователя на страницу "admin_home".
    """

    template_name = "master/login.html"
    authentication_form = AdminLoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):

        user = form.get_user()

        login(self.request, user)

        remember_me = form.cleaned_data.get("remember_me")
        if not remember_me:
            self.request.session.set_expiry(0)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("admin_home")


class AdminHomePageView(StaffCheckRequiredMixin, TemplateView):
    """
    Представление главной страницы администратора.

    Доступно только пользователям, прошедшим проверку StaffCheckRequiredMixin (т.е. сотрудникам/администраторам).
    Отображает шаблон master/home.html.
    """

    template_name = "master/home.html"


class StaffListView(StaffCheckRequiredMixin, FilterView):
    template_name = 'master/admin/staff.html'
    context_object_name = 'admins'
    filterset_class = StaffFilter
