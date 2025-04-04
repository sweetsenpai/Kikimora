from django.core.cache import cache
from ..models import *
from django.db.models import QuerySet


def user_bonus_cash():
    cash_key = 'bonus'
    bonus_cash = cache.get(cash_key)
    if not bonus_cash:
        bonus_cash = UserBonusSystem.objects.all()
        cache.set(cash_key, bonus_cash, timeout=60*15)
    return bonus_cash


def subcategory_cache(invalidate=False):
    cache_key = 'subcategory'

    # Если не нужно сбрасывать кеш и он есть — вернуть данные
    if not invalidate:
        sub_cache = cache.get(cache_key)
        print(sub_cache)
        if sub_cache:
            return sub_cache

    # Обновление кеша
    sub_cache = Subcategory.objects.filter(visibility=True)
    cache.set(cache_key, sub_cache)

    return sub_cache


def active_products_cache(subcategory_id: int = None, invalidate=False) -> QuerySet:
    """
    Возвращает кэшированные продукты. Если subcategory_id указан, возвращает товары для этой подкатегории.
    Если subcategory_id не указан, возвращает все видимые товары.

    Args:
        subcategory_id (int, optional): ID подкатегории для фильтрации товаров. По умолчанию None.
        invalidate (bool, optional): Если True, сбрасывает кеш перед получением данных.

    Returns:
        QuerySet: Список товаров.
    """
    cache_key = f'products_subcategory_{subcategory_id}' if subcategory_id else 'products'

    # Если кеширование не сбрасывается и кеш есть – возвращаем данные
    if not invalidate:
        product_cache = cache.get(cache_key)
        if product_cache:
            return product_cache

    # Запрос в базу
    queryset = Product.objects.filter(visibility=True)
    if subcategory_id:
        queryset = queryset.filter(subcategory__subcategory_id=subcategory_id)

    queryset = queryset.select_related('tag').order_by('name')

    # Обновляем кеш
    cache.set(cache_key, queryset)
    return queryset


def get_discounted_product_data(invalidate=False):
    cache_key = 'get_discounted_product_data'
    if not invalidate:
        dp_data = cache.get(cache_key)
        if dp_data is not None:
            return dp_data

    all_prices = cache.get("all_products_prices")
    products_with_discounts_ids = [product_id for product_id, discount in all_prices['discounts_map'].items() if discount]

    dp_data = active_products_cache().filter(product_id__in=products_with_discounts_ids)
    cache.set(cache_key, dp_data)
    return dp_data


def get_discount_cash(invalidate=False):
    cash_key = "discount"
    if not invalidate:
        disc_cash = cache.get(cash_key)
        if disc_cash:
            return disc_cash
    disc_cash = Discount.objects.filter(active=True)
    cache.set(cash_key, disc_cash)
    return disc_cash


def get_limit_product_cash(invalidate=False):
    cash_key = "limit"
    if not invalidate:
        limit_cash = cache.get(cash_key)
        if limit_cash:
            return limit_cash
    limit_cash = LimitTimeProduct.objects.all()
    cache.set(cash_key, limit_cash)
    return limit_cash