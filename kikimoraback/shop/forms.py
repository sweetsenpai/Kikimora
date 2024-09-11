# accounts/forms.py
from django import forms
from django.contrib.auth.models import Group
from django.contrib.auth.forms import ReadOnlyPasswordHashField, ValidationError
import re
from .models import *


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
        fields = ('email', 'user_fio', 'phone',
                  'bd', 'password', 'is_staff',
                  'is_superuser')

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


class CategoryCreationForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'text']

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name:
            raise ValidationError("Поле имя категории не может быть пустым")
        if Category.objects.filter(name=name).exists():
            raise ValidationError("Категория с таким названием уже существует, зачем вам ещё одна?")
        return name

    def clean_text(self):
        text = self.cleaned_data.get('text')
        return text


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ('name', 'photo_url', 'description',
                  'price', 'weight', 'bonus',
                  'visibility')
        error_messages = {
            'weight': {
                'required': "Поле вес не может быть пустым!",
                'invalid': "Введите корректное значение веса.",
            },
            'price': {
                'required': "Поле цена не может быть пустым!",
                'invalid': "Введите корректное значение цены.",
            },
            'name': {
                'required': "Поле названия не может быть пустым!",
            },
        }


class DiscountForm(forms.ModelForm):
    class Meta:
        model = Discount
        fields = ('discount_type', 'value', 'description',
                  'min_sum', 'start', 'end',
                  'category', 'subcategory', 'product')

    def clean(self):
        cleaned_data = super().clean()
        subcategory = cleaned_data.get('subcategory')
        product = cleaned_data.get('product')
        discount_type = cleaned_data.get('discount_type')
        value = cleaned_data.get('value')
        start = cleaned_data.get('start')
        end = cleaned_data.get('end')
        try:
            if discount_type == 'percentage' and value > 100:
                raise ValidationError({'value': 'Процент скидки не может быть больше 100!'})
        except TypeError:
                raise ValidationError({'value': 'Размер скидки не может быть равен 0!'})
        if start >= end:
            raise ValidationError({'start': 'Начало скидки не может быть равно или больше окончания, это просто не имеет смысла:/'})

        if product is not None:
            cleaned_data['category'] = None
            cleaned_data['subcategory'] = None

        if subcategory is not None and product is None:
            cleaned_data['category'] = None

        return cleaned_data


class PromocodeForm(forms.ModelForm):
    class Meta:
        model = PromoSystem
        fields = ('description', 'code', 'promo_product',
                  'type', 'min_sum', 'amount',
                  'one_time', 'start', 'end')
