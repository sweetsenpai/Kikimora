import logging

from celery import shared_task

from shop.MongoIntegration.Order import Order

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_payment_canceled(self, payment_id):
    try:
        user_order = Order()
        user_order_data = user_order.get_order_by_payment(payment_id)

        # Возврат бонусов
        if user_order_data["bonuses_deducted"]:
            UserBonusSystem.add_bonus(
                user_order_data["customer"], user_order_data["bonuses_deducted"]
            )
    except Exception as e:
        logger.error(f"Ошибка при обработке отмененного платежа {payment_id}: {e}")
        self.retry(countdown=2**self.request.retries)
