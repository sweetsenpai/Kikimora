from celery import shared_task
from shop.MongoIntegration.Order import Order
from shop.API.insales_api import send_new_order

import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_payment_succeeded(self, payment_id):
    try:
        user_order = Order()
        if not user_order.ping():
            logger.error(f"Ошибка подключения к базе данных при обработке платежа {payment_id}.")
            return

        user_order_data = user_order.get_order_by_payment(payment_id)

        # Начисление бонусов
        if user_order_data['add_bonuses']:
            UserBonusSystem.add_bonus(user_order_data['customer'], user_order_data['add_bonuses'])

        # Отправка заказа в InSales
        insales_order_new = send_new_order(user_order_data)
        if insales_order_new:
            user_order.insert_insales_number(payment_id=payment_id, insales_order_number=insales_order_new)
            user_order_data['insales'] = insales_order_new

            del user_order_data['_id']
            # Просто удалил поле _id воизбежания ошибки при сериализации=)

            new_order_email.delay(user_order_data)
        else:
            logger.error(f"Не удалось загрузить заказ {payment_id} в CRM.")
    except Exception as e:
        logger.error(f"Ошибка при обработке успешного платежа {payment_id}: {e}")
        self.retry(countdown=2 ** self.request.retries)  # Повторная попытка через экспоненциальное время ожидания
