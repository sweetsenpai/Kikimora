from yookassa import Configuration, Payment
from yookassa import Payment
import var_dump as var_dump
import os
import logging
from dotenv import load_dotenv
load_dotenv()
logger = logging.getLogger('shop')
key = 'test__kXJEEjyiSkZNQzUGm5nb5EwNtgjz4HHAIBXojqhYMU'
id = '1007767'

Configuration.configure(id, key)
res = Payment.create(
    {
        "amount": {
            "value": 1000,
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": "https://www.google.com"
        },
        "capture": True,
        "description": "Заказ №68",
        "metadata": {
            'orderNumber': '68'
        },
        "receipt": {
            "customer": {
                "full_name": "Ivanov Ivan Ivanovich",
                "email": "workchocolatemilk00@gmail.com",
                "phone": "79211234567",
            },
            "items": [
                {
                    "description": "Переносное зарядное устройство Хувей",
                    "quantity": "1.00",
                    "amount": {
                        "value": 80,
                        "currency": "RUB"
                    },
                    "vat_code": "2",
                    "payment_mode": "full_payment",
                    "payment_subject": "commodity",
                    "country_of_origin_code": "RU",
                },
            ]
        }
    }
)


class Payment:
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
                    "currency": "RUB"}})
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
                        "full_name": user_data.fio,
                        "email": user_data.email,
                        "phone": user_data.fio,
                    },
                    "items": items
                }
            })
        try:
            return payement.json()['confirmation']['confirmation_url'], payement.id
        except KeyError as e:
            logger.error(f"Ошибка при извлечении данных из ответа: {e}")
        except Exception as e:
            logger.critical(f"Не удалось создать оплату для клиента: {e}")
        return False
# print(res.json())
# var_dump.var_dump(res.)
# print(var_dump.var_dump(yookassa.Settings.get_account_settings()))