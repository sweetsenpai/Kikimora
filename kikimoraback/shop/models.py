import logging
from datetime import datetime, timedelta

import django.utils.timezone
from django.contrib.auth import get_user_model
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
    User,
)
from django.core.validators import (
    MaxLengthValidator,
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models
from django.utils import timezone

logger = logging.getLogger("shop")


class AccountManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, user_fio, password, **extra_fields):
        values = [email, user_fio]
        field_value_map = dict(zip(self.model.REQUIRED_FIELDS, values))
        for field_name, value in field_value_map.items():
            if not value:
                raise ValueError("The {} value must be set".format(field_name))
        email = self.normalize_email(email)
        user = self.model(email=email, user_fio=user_fio, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, user_fio, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, user_fio, password, **extra_fields)

    def create_superuser(self, email, user_fio, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, user_fio, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    user_id = models.AutoField(primary_key=True)
    email = models.EmailField(
        help_text="Ваш email",
        unique=True,
        db_index=True,
        error_messages={"unique": "Пользователь с таким email уже существует."},
    )
    user_fio = models.CharField(max_length=200, help_text="Ф.И.О.", db_index=True)
    phone = models.CharField(
        max_length=12,
        help_text="Номер телефона",
        unique=True,
        db_index=True,
        error_messages={
            "unique": "Пользователь с таким номером телефона уже существует."
        },
    )
    bd = models.DateField(default=timezone.now, help_text="Дата рождения")
    is_staff = models.BooleanField(default=False, help_text="")
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(null=True)
    is_email_verified = models.BooleanField(default=False)

    objects = AccountManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["user_fio", "phone"]

    def get_full_name(self):
        return self.user_fio

    def get_short_name(self):
        return self.user_fio.split()[0]

    def __str__(self):
        return f"{self.user_id}, {self.email}, {self.user_fio}, {self.phone}, {self.bd}"


class UserBonusSystem(models.Model):
    bonus_id = models.AutoField(primary_key=True)
    user_bonus = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="bonus"
    )
    bonus_ammount = models.IntegerField()

    def __str__(self):
        return f"{self.bonus_id}, {self.user_bonus}, {self.bonus_ammount}"

    @classmethod
    def add_bonus(cls, user_id: int, bonuses: int) -> None:
        """
        Начисляет бонусы пользователю. Если запись о пользователе не существует, то запись создается.
        """
        try:
            user = CustomUser.objects.get(user_id=user_id)
        except CustomUser.DoesNotExist:
            logger.error(
                f"Пользователь с id {user_id} не найден. Неудалось начислить баллы за заказ."
            )
            raise ValueError(f"Пользователь с id {user_id} не найден.")
        if user.is_email_verified:
            try:
                bonus_record, created = cls.objects.get_or_create(user_bonus=user)
                if not created:
                    bonus_record.bonus_ammount += bonuses
                    bonus_record.save()
                else:
                    bonus_record.bonus_ammount = bonuses
                    bonus_record.save()
            except Exception as e:
                raise ValueError(f"Ошибка при начислении бонусов: {e}")

    @classmethod
    def deduct_bonuses(cls, user_id, bonuses):
        """
        Списывает бонусы с аккаунта пользователя.
        """
        try:
            user = CustomUser.objects.get(user_id=user_id)
        except CustomUser.DoesNotExist:
            raise ValueError(f"Пользователь с id {user_id} не найден.")
        if user.is_email_verified:
            try:
                bonus_record = cls.objects.get(user_bonus=user)
            except cls.DoesNotExist:
                raise ValueError(
                    f"Запись о бонусах для пользователя с id {user_id} не найдена."
                )

            if bonus_record.bonus_ammount < bonuses:
                raise ValueError(
                    f"Ошибка при списании бонусов: Невозможно списать бонусов больше, чем есть у пользователя id {user_id}. Бонусов есть: {bonus_record.bonus_ammount}."
                    f"'\n Бонусов для списания:{bonuses}"
                )
            bonus_record.bonus_ammount -= bonuses
            bonus_record.save()


class UserAddress(models.Model):
    address_id = models.AutoField(primary_key=True)
    address_user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="address"
    )
    street = models.CharField(max_length=100, help_text="Улица", db_index=True)
    building = models.CharField(max_length=100, help_text="Дом", null=True, blank=True)
    apartment = models.CharField(
        max_length=100, help_text="Квартира", null=True, blank=True
    )

    def __str__(self):
        return f"{self.address_id}, {self.address_user}, {self.street}, {self.building}, {self.apartment}"


class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=200, help_text="Название категории", db_index=True, unique=True
    )
    text = models.CharField(max_length=400, help_text="Описание категории", blank=True)
    visibility = models.BooleanField(
        default=True, help_text="Указывает видимость категории"
    )

    def __str__(self):
        return f"{self.category_id}, {self.name}, {self.text}"


class Subcategory(models.Model):
    subcategory_id = models.AutoField(primary_key=True)
    name = models.CharField(
        max_length=200, help_text="Название подкатегории", db_index=True
    )
    text = models.TextField(help_text="Описание подкатегории", blank=True, null=True)
    visibility = models.BooleanField(
        default=True, help_text="Указывает видимость категории"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="subcategories",
        help_text="Основная категория",
    )
    permalink = models.CharField(max_length=200, default=None, null=True)

    def __str__(self):
        return f"{self.subcategory_id}, {self.name}, {self.text}, {self.category.name}"


class ProductTag(models.Model):
    tag_id = models.AutoField(primary_key=True)
    text = models.CharField(max_length=10)


class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, help_text="Название товара", db_index=True)
    description = models.TextField(default=None, null=True)
    price = models.FloatField(default=0.0, help_text="Цена товара")
    weight = models.FloatField(default=0.0, help_text="Вес товара в киллограммах")
    subcategory = models.ManyToManyField(Subcategory, related_name="products")
    bonus = models.IntegerField(default=0)
    visibility = models.BooleanField(
        default=True, help_text="Указывает видимость в выдаче"
    )
    permalink = models.CharField(max_length=200, default=None, null=True, db_index=True)
    available = models.BooleanField(default=True)
    tag = models.ForeignKey(ProductTag, null=True, blank=True, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.product_id}, {self.visibility}, {self.name}, {self.description}, {self.price}, {self.weight}, {self.subcategory}"


class ProductPhoto(models.Model):
    photo_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="photos"
    )
    photo_url = models.CharField(max_length=200, help_text="URL фотографии")
    is_main = models.BooleanField(
        default=False, help_text="Является ли эта фотография основной", null=True
    )
    photo_description = models.CharField(
        max_length=200, help_text="описание фотографии", null=True
    )


class ProductPhotoMini(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="mini_photos"
    )
    photo_url = models.CharField(max_length=200, help_text="URL фотографии")
    is_main = models.BooleanField(
        default=False, help_text="Является ли эта фотография основной", null=True
    )
    photo_description = models.CharField(
        max_length=200, help_text="описание фотографии", null=True
    )


class LimitTimeProduct(models.Model):
    limittimeproduct_id = models.AutoField(primary_key=True)
    product_id = models.ForeignKey(Product, on_delete=models.CASCADE)
    price = models.FloatField()
    ammount = models.IntegerField()
    due = models.DateTimeField()
    task_id = models.CharField(max_length=255, null=True, blank=True)


class Discount(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ("percentage", "Процентная"),
        ("amount", "Фиксированная"),
    ]

    discount_id = models.AutoField(primary_key=True)
    discount_type = models.CharField(
        max_length=15, choices=DISCOUNT_TYPE_CHOICES, default="percentage"
    )
    value = models.FloatField(help_text="Процент скидки или сумма скидки", default=0)
    description = models.CharField(max_length=400, blank=True)
    start = models.DateTimeField(default=django.utils.timezone.now())
    end = models.DateTimeField(default=django.utils.timezone.now())
    category = models.ForeignKey(
        Category, null=True, blank=True, on_delete=models.CASCADE
    )
    subcategory = models.ForeignKey(
        Subcategory, null=True, blank=True, on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        Product, null=True, blank=True, on_delete=models.CASCADE
    )
    active = models.BooleanField()
    task_id_start = models.CharField(max_length=255, null=True, blank=True)
    task_id_end = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.discount_id} - {self.value} ({self.get_discount_type_display()})"

    def apply_discount(self, price):
        if self.discount_type == "percentage":
            return round(price - (price * (self.value / 100)))
        elif self.discount_type == "amount":
            return max(0, price - self.value)
        return price


class PromoSystem(models.Model):
    PROMO_TYPE_CHOICES = [
        ("delivery", "Бесплатная доставка"),
        ("product_discount", "Скидка на товар"),
        ("cart_discount", "Скидка на корзину"),
    ]

    promo_id = models.AutoField(primary_key=True)
    description = models.CharField(max_length=400, blank=True, null=True)

    # Промокод, не более 10 символов, уникальный
    code = models.CharField(
        max_length=10,
        unique=True,
        validators=[
            MaxLengthValidator(10),
            RegexValidator(
                regex="^[A-Za-zА-Яа-я0-9]*$",
                message="Промокод должен состоять только из букв и цифр.",
            ),
        ],
        db_index=True,
    )

    # Промокод для конкретного товара (опционально)
    promo_product = models.ForeignKey(
        "Product", on_delete=models.CASCADE, blank=True, null=True
    )

    # Тип промокода
    type = models.CharField(max_length=20, choices=PROMO_TYPE_CHOICES)

    # Минимальная сумма для применения промокода
    min_sum = models.FloatField(
        default=1, validators=[MinValueValidator(0)], blank=True, null=True
    )

    # Для фиксированной скидки или процента (если используется скидка)
    amount = models.FloatField(blank=True, null=True)
    procentage = models.FloatField(blank=True, null=True)
    # Ограничения на использование
    usage_count = models.IntegerField(default=0)  # Количество использований
    one_time = models.BooleanField(
        default=False
    )  # Промокод на одноразовое использование

    # Время действия промокода
    start = models.DateTimeField(default=timezone.now)
    end = models.DateTimeField()
    task_id_start = models.CharField(max_length=255, null=True, blank=True)
    task_id_end = models.CharField(max_length=255, null=True, blank=True)
    active = models.BooleanField(default=True)

    def is_active(self):
        # Проверка на активность промокода по дате
        now = timezone.now()
        return self.start <= now <= self.end


class PromoCodeUseg(models.Model):
    promo_id = models.ForeignKey("PromoSystem", on_delete=models.CASCADE)
    user_id = models.ForeignKey("CustomUser", on_delete=models.CASCADE)
