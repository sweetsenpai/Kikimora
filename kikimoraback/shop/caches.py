from django.core.cache import cache
from .models import *


def get_products_sub_cash(cash_key, subcategory_id=None):
    product_sub_cash = cache.get(cash_key)
    if not product_sub_cash:
        product_sub_cash = Product.objects.filter(subcategory_id=subcategory_id, visibility=True)
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
        promo_cash = LimitTimeProduct.objects.select_related('product_id__subcategory__category').prefetch_related('product_id__photos')
        cache.set(cash_key, promo_cash, timeout=60*15)
    return promo_cash