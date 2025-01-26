from django.core.cache import cache
from .models import *
from .serializers import DiscountSerializer
from rest_framework.renderers import JSONRenderer
from django.db.models import QuerySet


def user_bonus_cash():
    cash_key = 'bonus'
    bonus_cash = cache.get(cash_key)
    if not bonus_cash:
        bonus_cash = UserBonusSystem.objects.all()
        cache.set(cash_key, bonus_cash, timeout=60*15)
    return bonus_cash


def subcategory_cash():
    cash_kay = 'subcategory'
    sub_cash = cache.get(cash_kay)
    if not sub_cash:
        sub_cash = Subcategory.objects.filter(visibility=True)
        cache.set(cash_kay, sub_cash, timeout=60*15)
    return sub_cash


def active_products_cash(subcategory_id: int = None)->QuerySet:
    """
        Возвращает кэшированные продукты. Если subcategory_id указан, возвращает товары для этой подкатегории.
        Если subcategory_id не указан, возвращает все видимые товары.

        Args:
            subcategory_id (int, optional): ID подкатегории для фильтрации товаров. По умолчанию None.

        Returns:
            QuerySet: Список товаров.
        """
    cash_key = f'products_subcategory_id_{subcategory_id}' if subcategory_id else 'products'

    product_cash = cache.get(cash_key)
    if not product_cash:
        if subcategory_id:
            product_cash = Product.objects.filter(subcategory__subcategory_id=subcategory_id).order_by('name')
        else:
            product_cash = Product.objects.filter(visibility=True)

        cache.set(cash_key, product_cash, timeout=60*15)
    return product_cash


def get_products_sub_cash(cash_key, subcategory_id=None):
    product_sub_cash = cache.get(cash_key)
    if not product_sub_cash:
        if subcategory_id:
            product_sub_cash = Product.objects.filter(subcategory__subcategory_id=subcategory_id, visibility=True)
        else:
            product_sub_cash = Product.objects.filter(visibility=True)

        cache.set(cash_key, product_sub_cash, timeout=60*15)
    return product_sub_cash


def get_discount_cash():
    cash_key = "discount"
    disc_cash = cache.get(cash_key)
    if not disc_cash:
        disc_cash = Discount.objects.filter(active=True)
        cache.set(cash_key, disc_cash, timeout=60*15)
    return disc_cash


def get_limit_product_cash():
    cash_key = "limit"
    limit_cash = cache.get(cash_key)
    if not limit_cash:
        limit_cash = LimitTimeProduct.objects.all()
        cache.set(cash_key, limit_cash, timeout=60 * 15)
    return limit_cash


def get_promo_cash():
    cash_key = "promo"
    promo_cash = cache.get(cash_key)

    if not promo_cash:
        # Используем prefetch_related для many-to-many связи
        promo_cash = LimitTimeProduct.objects.prefetch_related(
            'product_id__subcategory',  # Получаем связанные подкатегории для каждого товара
            'product_id__photos',  # Получаем фотографии товара
            'product_id__subcategory__category'  # Получаем связанные категории для каждой подкатегории
        )

        # Кешируем данные
        cache.set(cash_key, promo_cash, timeout=60 * 15)

    return promo_cash