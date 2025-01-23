from yookassa import Configuration, Payment
from yookassa import Receipt
import os
import logging
from dotenv import load_dotenv
from decimal import Decimal, ROUND_HALF_UP

load_dotenv()

logger = logging.getLogger('shop')
logger.setLevel(logging.DEBUG)

key = 'test__kXJEEjyiSkZNQzUGm5nb5EwNtgjz4HHAIBXojqhYMU'
id = '1007767'


class PaymentYookassa:
    def __init__(self):
        Configuration.configure(os.getenv("YOOMONEY_ID_2"), os.getenv("YOOMONEY_KEY_2"))

    def item_check_builder(self, cart: dict, delivery_data: dict, bonuses) -> list:
        """
            Создает список товаров и доставки для отправки на оплату.

            Args:
                cart (dict): Словарь с данными корзины. Ожидает ключи:
                    - products (list): список товаров с полями 'name', 'price', 'quantity'.
                    - total (float|Decimal): общая стоимость корзины.
                delivery_data (dict): Данные о доставке. Ожидает ключи:
                    - deliveryMethod (str): способ доставки.
                    - deliveryCost (float|Decimal): стоимость доставки.
                bonuses (float|Decimal): Количество бонусов для списания.

            Returns:
                list: Список товаров и услуги доставки в формате для оплаты.
            """
        bonuses = Decimal(bonuses or 0)
        remaining_bonuses = bonuses
        last_product = cart['products'][-1]
        items = []

        cart_total = Decimal(cart['total'])

        for product in cart['products']:
            product_price = Decimal(product['price'])

            if product != last_product:
                bonus_for_product = (product_price / cart_total * bonuses).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
                remaining_bonuses -= bonus_for_product
                items.append({
                    "description": product['name'],
                    "quantity": product['quantity'],
                    "amount": {
                        "value": (product_price - bonus_for_product ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        "currency": "RUB"
                    },
                    "vat_code": "1",
                    "payment_mode": "prepayment",
                    "payment_subject": "commodity",
                    "country_of_origin_code": "RU",
                    "measure": "piece"
                })
            else:
                items.append({
                    "description": product['name'],
                    "quantity": product['quantity'],
                    "amount": {
                        "value": (product_price - remaining_bonuses).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                        "currency": "RUB"
                    },
                    "vat_code": "1",
                    "payment_mode": "prepayment",
                    "payment_subject": "commodity",
                    "country_of_origin_code": "RU",
                    "measure": "piece"
                })

        delivery_cost = Decimal(delivery_data['deliveryCost'])
        items.append({
            "description": delivery_data['deliveryMethod'],
            "quantity": 1,
            "amount": {
                "value": delivery_cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                "currency": "RUB"
            },
            "vat_code": "1",
            "payment_mode": "prepayment",
            "payment_subject": "service",
        })

        return items

    def send_payment_request(self, user_data, cart, order_id, delivery_data, bonuses):
        bonuses = bonuses or 0

        payement = \
            Payment.create({
                "amount": {
                    "value": cart['total'] - bonuses,
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": os.getenv("PAYMENT_BACK_URL")
                },
                "capture": True,
                "description": f"Оплата №{order_id}",
                "receipt": {
                    "customer": {
                        "full_name": user_data['fio'],
                        "email": user_data['email'],
                        "phone": user_data['phone'],
                    },
                    "items": self.item_check_builder(cart, delivery_data, bonuses),

                }
            })
        try:
            logger.info(f"Платеж {order_id} успешно создан.")
            return payement.json()
        except KeyError as e:
            logger.error(f"Ошибка при извлечении данных из ответа yookassa: {e}")
        except Exception as e:
            logger.critical(f"Не удалось создать оплату для клиента. Данные корзины:{cart}\n ОШИБКА: {e}")
        return False


