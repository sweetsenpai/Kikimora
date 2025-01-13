from pymongo import MongoClient, ASCENDING
from collections import defaultdict
import logging
import json
from dotenv import load_dotenv
import os
load_dotenv()
logger = logging.getLogger('shop')


class Order:
    db_client = None

    def __init__(self, db_client=None):
        if Order.db_client is None:
            Order.db_client = db_client
        self.order_collection = Order.db_client["kikimora"]["order"]

    def ping(self):
        try:
            self.db_client.admin.command('ping')
            return True
        except Exception as e:
            logger.critical(f"Не удалось подключиться к mongodb.\n Errpr:{e}")
            return False

    def get_neworder_num(self):
        return int('420' + str(self.order_collection.count_documents({})+1))
