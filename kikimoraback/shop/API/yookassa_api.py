from yookassa import Configuration, Payment
from pymongo import MongoClient
from yookassa import Payment
from yookassa import Receipt
from ..MongoIntegration.Cart import Cart
import var_dump as var_dump
import os
import logging
from dotenv import load_dotenv
import random
load_dotenv()
logger = logging.getLogger('shop')
key = 'test__kXJEEjyiSkZNQzUGm5nb5EwNtgjz4HHAIBXojqhYMU'
id = '1007767'
# order_num = random.random()
# Configuration.configure(id, key)
# res = Payment.create(
#     {
#         "amount": {
#             "value": 1000,
#             "currency": "RUB"
#         },
#         "confirmation": {
#             "type": "redirect",
#             "return_url": "https://2ch.hk/b"
#         },
#         "capture": True,
#         "description": f"Заказ №{order_num}",
#         "metadata": {
#             'orderNumber': f'{order_num}'
#         },
#         "receipt": {
#             "customer": {
#                 "full_name": "Ivanov Ivan Ivanovich",
#                 "email": "workchocolatemilk00@gmail.com",
#                 "phone": "79211234567",
#                 "inn": "6321341814"
#             },
#             "items": [
#                 {
#                     "description": "Переносное зарядное устройство Хувей",
#                     "quantity": "1.00",
#                     "amount": {
#                         "value": 1000,
#                         "currency": "RUB"
#                     },
#                     "vat_code": "1",
#                     "payment_mode": "full_payment",
#                     "payment_subject": "commodity",
#                     "country_of_origin_code": "CN",
#                     "measure": "piece"
#                 },
#             ]
#         }
#     }
# )


class PaymentYookassa:
    def __init__(self):
        Configuration.configure(os.getenv('YOOMONEY_ID'), os.getenv('YOOMONEY_KEY'))

    def send_payment_request(self, user_data, cart, order_id):
        items=[]
        for product in cart['products']:
            items.append({
                "description": product['name'],
                "quantity": product['quantity'],
                "amount": {
                    "value": product['price'],
                    "currency": "RUB"},
                "vat_code": "1",
                "payment_mode": "full_payment",
                "payment_subject": "commodity",
                "country_of_origin_code": "RU",
                "measure": "piece"
                }
                )
        payement = \
            Payment.create({
                "amount": {
                    "value": cart['total'],
                    "currency": "RUB"
                },
                "confirmation": {
                    "type": "redirect",
                    "return_url": "sucsess url"
                },
                "capture": True,
                "description": f"Заказ №{order_id}",
                "metadata": {
                    'orderNumber': f'{order_id}'
                },
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
            return payement.json()['confirmation']['confirmation_url'], payement.id
        except KeyError as e:
            logger.error(f"Ошибка при извлечении данных из ответа: {e}")
        except Exception as e:
            logger.critical(f"Не удалось создать оплату для клиента: {e}")
        return False


cart = Cart(MongoClient(os.getenv("MONGOCON")))
cart_data = cart.get_cart_data(user_id=1)
print(cart_data)
# payement = PaymentYookassa()
# payement.send_payment_request(user_data={'fio': "Захаров Александр", "email": 'test@mail.ru',"phone": '+79118468177'},
#                               cart=cart_data, order_id=random.random())