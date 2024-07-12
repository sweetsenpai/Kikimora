from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import datetime
status_dict ={"NEW": "НОВЫЙ", "IN PROGRESS": "В РАБОТЕ",
              "DELIVERY": "ДОСТАВКА", "COMPLETE": "ВЫПОЛНЕН",
              "DECLINED": "ОТМЕНЕН", "AWAITING PAYMENT": "ОЖИДАЕТ ОПЛАТЫ"}


class CustomUser(AbstractUser):
    user_id = models.AutoField(primary_key=True)
    user_fio = models.CharField(max_length=200, help_text='Ф.И.О.')
    phone = models.CharField(max_length=9, help_text='Номер телефона')
    bd = models.DateField(default=datetime.now().date(), help_text='Дата рождения')
# TODO: Система индивидуальных скидок или баллов


class UserAddress(models.Model):
    address_id = models.AutoField(primary_key=True)
    address_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    street = models.CharField(max_length=100, help_text='Улица')
    building = models.CharField(max_length=100, help_text='Дом')
    apartment = models.CharField(max_length=100, help_text='Квартира')


class OrdersHistory(models.Model):
    order_id = models.AutoField(primary_key=True)
    order_user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    creation_time = models.DateTimeField(default=datetime.now(), help_text='Дата создания')
    prefer_delivery_time= models.DateTimeField(default=None, help_text='Дата и время доставка выбранное пользователем')
    actual_delivery_time = models.DateTimeField(default=None, help_text=' Фактическая дата и время доставка')
    status = models.CharField(choices=status_dict)
    text = models.CharField(max_length=1000, blank=True, help_text="Дополнительные пожелания к Вашему заказу")
    composition = models.CharField(max_length=1000)
    address = models.ForeignKey(UserAddress, on_delete=models.CASCADE)


class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, help_text='Название категории')
    text = models.CharField(max_length=400, help_text='Описание категории', blank=True)


class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    active = models.BooleanField(help_text='Продукт доступен в продаже')
    name = models.CharField(max_length=200, help_text='Название товара')
    photo_url = models.CharField(max_length=100, default=None)
    composition = models.CharField(max_length=400, default=None)
    price = models.FloatField(default=0.0, help_text='Цена товара')
    weight = models.FloatField(default=0.0, help_text='Вес товара в киллограммах')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)


class Discount(models.Model):
    discount_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    percentage = models.IntegerField(default=0, help_text='Процент скидки')
    amount = models.IntegerField(default=0, help_text='Сумма скидки')
# TODO: Уточнить о системе скидок