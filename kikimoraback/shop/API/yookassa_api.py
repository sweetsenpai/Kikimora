from yookassa import Configuration, Payment
from pymongo import MongoClient
from yookassa import Payment
from yookassa import Receipt
import var_dump as var_dump
import os
import logging
from dotenv import load_dotenv
import random
load_dotenv()
logger = logging.getLogger('shop')
logger.setLevel(logging.DEBUG)
key = 'test__kXJEEjyiSkZNQzUGm5nb5EwNtgjz4HHAIBXojqhYMU'
id = '1007767'


class PaymentYookassa:
    def __init__(self):
        Configuration.configure('1007767', 'test__kXJEEjyiSkZNQzUGm5nb5EwNtgjz4HHAIBXojqhYMU')

    def send_payment_request(self, user_data, cart, order_id, delivery_data, bonuses):
        bonuses = bonuses or 0
        items=[]
        for product in cart['products']:
            items.append({
                "description": product['name'],
                "quantity": product['quantity'],
                "amount": {
                    "value": round(product['price'] - ((product['price']/cart['total']) * bonuses)),
                    "currency": "RUB"},
                "vat_code": "1",
                "payment_mode": "prepayment",
                "payment_subject": "commodity",
                "country_of_origin_code": "RU",
                "measure": "piece"
                }
                )
        items.append({
            "description": delivery_data['deliveryMethod'],
            "quantity": 1,
            "amount": {
                "value": delivery_data['deliveryCost'],
                "currency": "RUB"},
            "vat_code": "1",
            "payment_mode": "prepayment",
            "payment_subject": "service",
        }
        )
        payement = \
            Payment.create({
                "amount": {
                    "value": cart['total'] - bonuses,
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": "http://localhost:3000/"
                },
                "capture": True,
                "description": f"Оплата №{order_id}",
                "receipt": {
                    "customer": {
                        "full_name": user_data['fio'],
                        "email": user_data['email'],
                        "phone": user_data['phone'],
                    },
                    "items": items,

                }
            })
        try:
            logger.info(f"Платеж {order_id} успешно создан.")
            return payement.json()
        except KeyError as e:
            logger.error(f"Ошибка при извлечении данных из ответа: {e}")
        except Exception as e:
            logger.critical(f"Не удалось создать оплату для клиента: {e}")
        return False


