from django.contrib.auth import get_user_model, login
from django.contrib.auth.views import LoginView
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render
from django.urls import reverse_lazy
from django.utils.crypto import get_random_string
from django.views import View
from django.views.generic import FormView, TemplateView

from django_filters.views import FilterView

from shop.filters import StaffFilter
from shop.forms import AdminCreationForm, AdminLoginForm
from shop.mixins import StaffCheckRequiredMixin
from shop.services.admin_demolition import AdminDemotionService
from shop_api.tasks import new_admin_mail


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
    """
    Представление для отображения списка сотрудников (staff-пользователей и суперпользователей).

    Доступ к представлению ограничен с помощью миксина StaffCheckRequiredMixin,
    который пускает только аутентифицированных пользователей с правами is_staff или is_superuser.

    Использует django-filter для фильтрации списка по полям: ФИО, email и номер телефона.

    Атрибуты:
        template_name (str): Путь к HTML-шаблону для отображения списка.
        context_object_name (str): Имя переменной контекста, в которую будет передан список сотрудников.
        filterset_class (FilterSet): Класс фильтрации, определяющий фильтруемые поля.

    Шаблон: templates/master/admin/staff.html
    """

    template_name = "master/admin/staff.html"
    context_object_name = "admins"
    filterset_class = StaffFilter


class AdminCreateView(StaffCheckRequiredMixin, FormView):
    """
    Представление для создания нового администратора через форму.

    Поведение:
    - При валидной форме создается новый пользователь с правами администратора,
      генерируется случайный пароль и отправляется письмо на почту.
    - Если форма невалидна, но пользователь с таким email уже существует,
      его статус обновляется (назначается is_staff, is_superuser) и также отправляется письмо.
    - В остальных случаях возвращаются ошибки формы в формате JSON.

    Используется только в админке и не предполагает переиспользования логики вне этого контекста.
    """

    template_name = "master/admin/admin_creation_page.html"
    form_class = AdminCreationForm
    success_url = reverse_lazy("staff")

    def form_valid(self, form):
        user_fio = form.cleaned_data["user_fio"]
        email = form.cleaned_data["email"]
        phone = form.cleaned_data["phone"]
        is_superuser = form.cleaned_data["is_superuser"]
        new_user = get_user_model()(
            user_fio=user_fio,
            email=email,
            phone=phone,
            is_superuser=is_superuser,
            is_staff=True,
        )
        password = get_random_string(20)
        new_user.set_password(password)
        new_user.save()
        new_admin_mail.delay(password, new_user.email)
        return JsonResponse({"status": "success", "redirect_url": self.success_url})

    def form_invalid(self, form):
        """Если email или телефон уже существуют, вместо ошибки обновляем существующего пользователя."""
        email = form.data.get("email")
        existing_user = get_user_model().objects.filter(email=email).first()

        if existing_user:
            # Если пользователь найден → обновляем его статусы и отправляем письмо
            existing_user.is_superuser = form.data.get("is_superuser", False)
            existing_user.is_staff = True
            existing_user.save()

            new_admin_mail.delay("Ваш текущий пароль остается неизменным.", existing_user.email)

            return JsonResponse({"status": "success", "redirect_url": self.success_url})
        errors = {field: error_list[0] for field, error_list in form.errors.items()}
        return JsonResponse({"status": "error", "errors": errors})


class AdminAccountView(StaffCheckRequiredMixin, View):
    template_name = "master/admin/admin_page.html"
    success_url = "/apanel/staff"

    def get_admin(self, admin_id):
        return get_object_or_404(get_user_model(), user_id=admin_id, is_staff=True)

    def get(self, request, admin_id):
        admin = self.get_admin(admin_id)
        return render(request, self.template_name, context={"admin": admin})

    def post(self, request, admin_id):
        admin = self.get_admin(admin_id)
        try:
            AdminDemotionService(admin).execute()
            return JsonResponse({"status": "success", "redirect_url": self.success_url})
        except ValueError as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)
