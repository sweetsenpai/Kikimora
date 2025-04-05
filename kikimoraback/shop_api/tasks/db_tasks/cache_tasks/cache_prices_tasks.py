import logging
from functools import wraps

from celery import shared_task

from shop.services.caches import *
from shop.services.price_calculation import calculate_prices


def cache_result(cache_key: str, timeout: int = None):
    """
    Декоратор для кэширования.

    :param cache_key: Ключ для хранения результата в кэше.
    :param timeout: Время жизни кэша в секундах. Если None, кэш будет вечным.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Извлекаем параметр forced из kwargs, если он есть
            forced = kwargs.pop("forced", False)

            # Проверяем, есть ли результаты в кэше
            cached_result = cache.get(cache_key)
            if cached_result is not None and not forced:
                return cached_result
            # Кэшируем полученные данные и сохраняем
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout=timeout)
            return result

        return wrapper

    return decorator


@shared_task
@cache_result("all_products_prices", timeout=None)
def update_price_cache(forced=False):
    """
    Фоновая задача для предрасчета цен товаров.
    :param forced: Используется для принудительного создания нового кэша, даже если он есть. По умолчанию false.
    """
    products = active_products_cache()
    result = calculate_prices(products)
    logger.info("Кэширование цен товаров прошло успешно.")
    return result
