import logging

from celery import shared_task

from shop.services.caches import LimitTimeProduct

logger = logging.getLogger(__name__)


@shared_task
def delete_limite_time_product(product_id):
    product = LimitTimeProduct.objects.filter(product_id=product_id).first()
    if not product:
        logger.warning(f"Товар дня id:{product_id} не существует в БД.")
        return

    product.delete()
    logger.warning(f"Товар дня id:{product_id} удалён.")
    return
