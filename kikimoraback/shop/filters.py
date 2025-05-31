import django_filters
from django import forms
from django.db.models import Q
from django.contrib.auth import get_user_model

class StaffFilter(django_filters.FilterSet):
    user_fio = django_filters.CharFilter(field_name='user_fio', lookup_expr='icontains',
                                       label='ФИО',
                                       widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Фамилия'}))

    email = django_filters.CharFilter(field_name='email', lookup_expr='icontains',
                                     widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    phone = django_filters.CharFilter(field_name='phone', lookup_expr='icontains',
                                     widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Номер телефона'}))

    class Meta:
        model = get_user_model()
        fields = ['user_fio',  'email', 'phone']

    @property
    def qs(self):
        return super().qs.filter(is_staff=True)
