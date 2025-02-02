import requests
import json
from dotenv import load_dotenv
import os
from pymongo import MongoClient
from datetime import datetime
import logging

load_dotenv()
logger = logging.getLogger('shop')


def prep_time(time_string: str) -> dict:
    """Парсит временной диапазон в формате 'HH:MM-HH:MM'."""
    time_list = time_string.split("-")
    from_hour, from_minute = map(int, time_list[0].split(":"))
    to_hour, to_minute = map(int, time_list[1].split(":"))
    return {'from_hour': from_hour,
            'from_minutes': from_minute,
            'to_hour': to_hour,
            'to_minutes': to_minute}

# TODO при формировании заказа с доставкой не ставиться корректная цена из бд.
# TODO решить как отображать бонусы использованные при оформлении заказа.
def send_new_order(data):
    if data['delivery_data']['method'] == 'Самовывоз':
        addres = "11-ая Красноармейская, д.11 стр. 3 Мастерская Кикимора"
        delivery_variant = os.getenv("SELF_DELIVERY_CODE")
    else:
        addres = f"{data['delivery_data']['street']}, " \
                 f"{data['delivery_data']['building']}, кв." \
                 f"{data['delivery_data']['apartment']}"
        delivery_variant = os.getenv("DELIVERY_CODE")

    time_rang = prep_time(data['delivery_data']['time'])

    product_list = []
    for product in data['products']:
        product_list.append({
            "product_id": product['product_id'],
            "quantity": product['quantity'],
            "sale_price": product['price'],
        })

    order_request = {
        "order": {
            "custom_status_permalink": "v-obrabotke",
            "order_lines_attributes": product_list,
            "client": {
                "name": data['customer_data']['fio'],
                "email": data['customer_data']['email'],
                "phone": data['customer_data']['phone'],
                "consent_to_personal_data": True
            },
            "shipping_address_attributes": {
                "address": addres,
                "date": "12.02.2024",
                "time": "13:00",
                "full_locality_name": "Санкт-Петербург"
            },
            "shipping_price": data['delivery_data']['cost'],
            "payment_gateway_id": os.getenv("PAYMENT_GETAWAY_ID"),
            "coupon": None,
            "source": "Сайт",
            "delivery_variant_id": delivery_variant,
            'delivery_date': data['delivery_data']['date'].strftime("%Y-%m-%d"),
            'delivery_from_hour': time_rang['from_hour'],
            'delivery_from_minutes': time_rang['from_minutes'],
            'delivery_to_hour': time_rang['to_hour'],
            'delivery_to_minutes': time_rang['to_minutes'],
            'delivery_price': data['delivery_data']['cost'],
            'financial_status': 'paid',
            'comment': data['comment'],
            "manager_comment": f"Начислено бонусов: {data.get('add_bonuses', 0)}, списано бонусов: {data.get('bonuses_deducted', 0)}",

        }
    }

    base_url = os.getenv("INSALES_URL") + "orders.json"
    response = requests.post(base_url, json=order_request)
    if response.status_code == 201:
        return response.json()['number']
    else:
        logger.critical(f"по какой-то причине не удалось загрузить заказ в CRM! Ответ CRM:{response.json()}")
        return False
