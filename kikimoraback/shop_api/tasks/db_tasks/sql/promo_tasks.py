from celery import shared_task
import logging
from shop.services.caches import PromoSystem

logger = logging.getLogger(__name__)


@shared_task
def activate_promo(promo_id):
    promo = PromoSystem.objects.filter(promo_id=promo_id).first()
    if not promo:
        logger.warning(f'Промокод с id {promo_id} не существует в БД.')
        return
    promo.active = False
    promo.save()
    logger.info(f'Промокод с id {promo_id} теперь активен.')
    return


@shared_task
def deactivate_expired_promo(promo_id):
    promo = PromoSystem.objects.filter(promo_id=promo_id).first()
    if not promo:
        logger.warning(f'Промокод с id {promo_id} не существует в БД.')
        return
    promo.active = False
    promo.save()
    logger.info(f'Промокод с id {promo_id} теперь не активен.')
    return
