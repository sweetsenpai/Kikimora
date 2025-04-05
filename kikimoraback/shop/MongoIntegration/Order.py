import datetime
import hashlib
import json
import logging
import os
from collections import defaultdict

from bson import json_util
from dotenv import load_dotenv
from pymongo import ASCENDING, MongoClient

from ..MongoIntegration.db_connection import MongoDBClient

load_dotenv()
logger = logging.getLogger("shop")


# TODO: добавить индексы для коллекции заказов
class Order:
    def __init__(self):
        self.db_client = MongoDBClient.get_client()
        self.order_collection = self.db_client["kikimora"]["order"]

    def ping(self):
        try:
            self.db_client.admin.command("ping")
            return True
        except Exception as e:
            logger.critical(f"Не удалось подключиться к mongodb.\n Errpr:{e}")
            return False

    def create_order_on_cart(self, cart_data):
        cart_data["status"] = "NEW"
        self.order_collection.insert_one(cart_data)
        return

    def get_neworder_num(self, user_id):
        hash_string = f"{user_id}-{datetime.datetime.now()}"
        order_hash = hashlib.md5(hash_string.encode()).hexdigest()
        return int(str(int(order_hash, 16))[-6:])

    def get_users_orders(self, user_id):
        """
        Возвращает все заказы пользователя.
        Args:
            user_id: ID пользователя
        """
        user_orders_cursor = self.order_collection.find(
            {"customer": user_id}, {"_id": 0, "customer": 0, "payment_id": 0}
        ).sort("insales")
        return list(user_orders_cursor)

    def get_order_by_payment(self, payment_id=str) -> dict | bool:
        """
        Получение заказа по id платежа
        Args:
            payment_id :  ID платежа
        """
        order_data = self.order_collection.find_one({"payment_id": payment_id})
        if order_data is None:
            return False
        return order_data

    def insert_insales_number(self, payment_id: str, insales_order_number: int) -> bool:
        """
        Присвоение заказу номера из Insales.
        Args:
            payment_id :  ID платежа
            insales_order_number: Номер заказа переданый insales.
        """
        try:
            updated_order = self.order_collection.find_one_and_update(
                {"payment_id": payment_id},
                {"$set": {"insales": insales_order_number, "status": "PAYED"}},
            )
            if not updated_order:
                logger.error(f"Не удалось найти заказ с ID оплаты {payment_id}")
                return False
            else:
                return True
        except Exception as e:
            logger.error(
                "По какой-то причине произошла ошибка при присвоении заказа номера из insales.\n"
                f"ID payment: {payment_id}\n"
                f"ERROR: {e}"
            )
            return False
