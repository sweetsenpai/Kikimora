from typing import Any

from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import AbstractBaseUser
from django.http import HttpResponseRedirect
from django.shortcuts import redirect


def is_staff_or_superuser(user: AbstractBaseUser) -> bool:
    """
    Проверяет, является ли пользователь аутентифицированным и имеет ли статус is_staff или is_superuser.

    Args:
        user (AbstractBaseUser): Объект пользователя.

    Returns:
        bool: True, если пользователь авторизован и является staff или superuser, иначе False.
    """
    return user.is_authenticated and (user.is_staff or user.is_superuser)


class StaffCheckRequiredMixin(UserPassesTestMixin):
    """
    Миксин для ограничения доступа только для пользователей, имеющих статус is_staff или is_superuser.

    Наследуется от UserPassesTestMixin и переопределяет test_func для реализации пользовательской логики доступа.
    В случае отказа в доступе перенаправляет пользователя на страницу входа администратора.
    """

    def test_func(self) -> bool:
        """
        Проверяет, соответствует ли пользователь требованиям: is_staff или is_superuser.

        Returns:
            bool: True, если пользователь имеет права доступа, иначе False.
        """
        return is_staff_or_superuser(self.request.user)

    def handle_no_permission(self) -> HttpResponseRedirect:
        """
        Обрабатывает ситуацию, когда пользователь не имеет прав доступа.

        Returns:
            HttpResponseRedirect: Перенаправление на страницу входа администратора.
        """
        return redirect("admin_login")
