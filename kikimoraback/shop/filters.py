from django import forms
from django.contrib.auth import get_user_model

import django_filters

from shop.views_admin.views_admin import is_staff_or_superuser


class StaffFilter(django_filters.FilterSet):
    """
    Фильтр для выборки пользователей с ролью персонала или суперпользователя.

    Позволяет фильтровать пользователей по следующим полям:

    - `user_fio`: фильтрация по ФИО (частичное совпадение, регистронезависимое).
    - `email`: фильтрация по email (частичное совпадение, регистронезависимое).
    - `phone`: фильтрация по телефону (частичное совпадение).

    Все поля используют виджеты с подсказками и стилизованы через CSS-класс 'form-control'.
    Возвращает только пользователей, у которых `is_staff=True` или `is_superuser=True`.

    Атрибуты:
        user_fio (CharFilter): Фильтр по полному имени пользователя.
        email (CharFilter): Фильтр по email адресу.
        phone (CharFilter): Фильтр по номеру телефона.
    """

    user_fio = django_filters.CharFilter(
        field_name="user_fio",
        lookup_expr="icontains",
        label="ФИО",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "Фамилия Имя Отчество"}
        ),
    )

    email = django_filters.CharFilter(
        field_name="email",
        lookup_expr="icontains",
        label="Email",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "email@example.com"}),
    )

    phone = django_filters.CharFilter(
        field_name="phone",
        lookup_expr="icontains",
        label="Телефон",
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": "+7 (___) ___-__-__"}
        ),
    )

    class Meta:
        model = get_user_model()
        fields = ["user_fio", "email", "phone"]

    @property
    def qs(self):
        parent = super().qs
        return parent.filter(is_staff=True) | parent.filter(is_superuser=True)
