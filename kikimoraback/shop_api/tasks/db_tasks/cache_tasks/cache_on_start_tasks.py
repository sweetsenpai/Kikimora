import logging

from celery import shared_task

from shop.services.caches import *

from .cache_prices_tasks import update_price_cache

logger = logging.getLogger(__name__)


@shared_task
def boot_cache():
    if not cache.get("is_cache_initialized"):
        logger.info("Начинаю загрузку кэш!")
        active_products_cache(True)
        subcategory_cache(True)
        get_discount_cash(True)
        get_limit_product_cash(True)
        update_price_cache(True)
        get_discounted_product_data(True)
        cache.set("is_cache_initialized", True)
        logger.info("Кэш загружен!")
