import logging

from celery import shared_task

from shop.services.caches import Discount

logger = logging.getLogger(__name__)


@shared_task
def activate_discount(discount_id):
    discount = Discount.objects.filter(discount_id=discount_id).first()
    if not discount:
        logger.warning(f"Скидки с указаным id:{discount_id} не существует в БД.")
        return
    discount.active = True
    discount.save()
    logger.info(f"Скдка с id {discount_id} активирована.")
    return


@shared_task
def deactivate_expired_discount(discount_id):
    discount = Discount.objects.filter(discount_id=discount_id).first()
    if not discount:
        logger.warning(f"Скидки с указаным id:{discount_id} не существует в БД.")
        return
    discount.active = False
    discount.save()
    logger.info(f"Скдка с id {discount_id} удалена.")
    return
