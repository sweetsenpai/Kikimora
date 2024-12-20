from django.core.cache import cache
from .models import *


def get_products_sub_cash(cash_key, subcategory_id=None):
    product_sub_cash = cache.get(cash_key)
    if not product_sub_cash:
        if subcategory_id:
            # Используем фильтрацию по связи many-to-many через subcategories
            product_sub_cash = Product.objects.filter(subcategory__subcategory_id=subcategory_id, visibility=True)
        else:
            # Если subcategory_id не передан, просто фильтруем по visibility
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