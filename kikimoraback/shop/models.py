from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import MaxValueValidator
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import models
from datetime import datetime


class AccountManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, user_fio, password, **extra_fields):
        values = [email, user_fio]
        field_value_map = dict(zip(self.model.REQUIRED_FIELDS, values))
        for field_name, value in field_value_map.items():
            if not value:
                raise ValueError('The {} value must be set'.format(field_name))
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            user_fio=user_fio,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, user_fio, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, user_fio, password, **extra_fields)

    def create_superuser(self, email, user_fio, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, user_fio, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)
    email = models.EmailField(help_text="Ваш email", unique=True, db_index=True)
    user_fio = models.CharField(max_length=200, help_text='Ф.И.О.', db_index=True)
    phone = models.CharField(max_length=12, help_text='Номер телефона', db_index=True)
    bd = models.DateField(default=timezone.now, help_text='Дата рождения')
    is_staff = models.BooleanField(default=False, help_text='')
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True)

    objects = AccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['user_fio', 'phone']

    def get_full_name(self):
        return self.user_fio

    def get_short_name(self):
        return self.user_fio.split()[0]

    def __str__(self):
        return f"{self.user_id}, {self.email}, {self.user_fio}, {self.phone}, {self.bd}"


class UserBonusSystem(models.Model):
    bonus_id = models.AutoField(primary_key=True)
    user_bonus = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    bonus_ammount = models.IntegerField()

    def __str__(self):
        return f"{self.bonus_id}, {self.user_bonus}, {self.bonus_ammount}"


class UserAddress(models.Model):
    address_id = models.AutoField(primary_key=True)
    address_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    street = models.CharField(max_length=100, help_text='Улица', db_index=True)
    building = models.CharField(max_length=100, help_text='Дом')
    apartment = models.CharField(max_length=100, help_text='Квартира')

    def __str__(self):
        return f"{self.address_id}, {self.address_user}, {self.street}, {self.building}, {self.apartment}"


# Возможно нужно удалить эту таблицу и полностью заменить на mongodb
class OrdersHistory(models.Model):
    order_id = models.AutoField(primary_key=True)
    order_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.order_id},{self.order_user}"


class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, help_text='Название категории', db_index=True)
    text = models.CharField(max_length=400, help_text='Описание категории', blank=True)

    def __str__(self):
        return f"{self.category_id}, {self.name}, {self.text}"


class Subcategory(models.Model):
    subcategory_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, help_text='Название подкатегории', db_index=True)
    text = models.CharField(max_length=400, help_text='Описание подкатегории', blank=True)


class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    active = models.BooleanField(help_text='Продукт доступен в продаже')
    name = models.CharField(max_length=200, help_text='Название товара', db_index=True)
    photo_url = models.CharField(max_length=100, default=None)
    composition = models.CharField(max_length=400, default=None)
    price = models.FloatField(default=0.0, help_text='Цена товара')
    weight = models.FloatField(default=0.0, help_text='Вес товара в киллограммах')
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE)
    bonus = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product_id}, {self.active}, {self.name}, {self.photo_url}, {self.composition}, {self.price}, {self.weight}, {self.category}"


class LimitTimeProduct(models.Model):
    limittimeproduct_id = models.AutoField(primary_key=True)
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    ammount = models.IntegerField()
    due = models.DateTimeField()


class Discount(models.Model):
    discount_id = models.AutoField(primary_key=True)
    percentage = models.IntegerField(default=0, help_text='Процент скидки', blank=True)
    amount = models.IntegerField(default=0, help_text='Сумма скидки', blank=True)
    description = models.CharField(max_length=400, blank=True)
    min_sum = models.FloatField(default=1, blank=True)

    def __str__(self):
        return f"{self.discount_id}, {self.product},{self.percentage}, {self.amount}, {self.description}"


class DiscountCategory(models.Model):
    discountcategory_id = models.AutoField(primary_key=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    due = models.DateTimeField()


class DiscountSubcategory(models.Model):
    discountsubcategory_id = models.AutoField(primary_key=True)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE)
    due = models.DateTimeField()


class DiscountProduct(models.Model):
    discountproduct_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    due = models.DateTimeField()


class PromoSystem(models.Model):
    promo_id = models.AutoField(primary_key=True)
    creator = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    promo_product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True)
    type = models.CharField(max_length=50)
    min_sum = models.FloatField(default=1, blank=True)
    useg = models.IntegerField()
    one_time = models.BooleanField
    due = models.DateTimeField()


class PromoUser(models.Model):
    promouser_id = models.AutoField(primary_key=True)
    code = models.ForeignKey(PromoSystem, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)