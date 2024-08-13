# accounts/forms.py
from django import forms
from django.contrib.auth.models import Group
from django.contrib.auth.forms import ReadOnlyPasswordHashField, ValidationError
import re

from .models import CustomUser


class RegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Password', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('email', 'user_fio', 'phone', 'bd', 'password')

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = CustomUser
        fields = ('email', 'user_fio', 'phone', 'bd', 'password', 'is_staff', 'is_superuser')

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Пароли не совпадают")
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = CustomUser
        fields = ('email', 'user_fio', 'phone', 'bd', 'password', 'is_staff', 'is_superuser')

    def clean_password(self):
        return self.initial["password"]


class AdminCreationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['email', 'user_fio', 'phone', 'is_superuser']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError("Данный email уже существует в базе данных.")
        return email

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if not re.match(r'^\+?[1-9]\d{1,14}$', phone):
            raise ValidationError("Введите корректный номер телефона.")
        if CustomUser.objects.filter(phone=phone).exists():
            raise ValidationError("Данный номер телефона уже в базе данных.")
        return phone