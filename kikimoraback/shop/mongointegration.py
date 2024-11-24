from pymongo import MongoClient
import os
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
load_dotenv()

client = MongoClient(os.environ.get("MONGOCON"))
db = client['kikimora']
cart = db['cart']
cart.create_index(['order_id', 'order_user', 'creation_time', 'address'])


class OrderMongo:
    def __init__(self, order_id: int, order_user=None, prefer_delivery_time=None, actual_delivery_time=None, status=None, text=None, address=None, composition=None, creation_time=datetime.now(timezone(timedelta(hours=3))).replace(microsecond=0, tzinfo=None)):
        order_data = cart.find_one({'order_id': order_id})
        if order_data is None:
            self.order_id = order_id
            self.order_user = order_user
            self.creation_time = creation_time
            self.prefer_delivery_time = prefer_delivery_time
            self.actual_delivery_time = actual_delivery_time
            self.status = status
            self.text = text
            self.composition = composition
            self.address = address

        else:
            self.order_id = order_id
            self.order_user = order_data['order_user']
            self.creation_time = order_data['creation_time']
            self.prefer_delivery_time = order_data['prefer_delivery_time']
            self.actual_delivery_time = order_data['actual_delivery_time']
            self.status = order_data['status']
            self.text = order_data['text']
            self.composition = order_data['composition']
            self.address = order_data['address']

    def __str__(self):
        return f"'order_id': {self.order_id}, 'order_user': {self.order_user}, 'creation_time': {self.creation_time}," \
               f"'prefer_delivery_time': {self.prefer_delivery_time}, 'actual_delivery_time': {self.actual_delivery_time}," \
               f"'status': {self.status}, 'text': {self.text}, 'address': {self.address}, 'composition': {self.composition}"

    def create_new_order(self):
        cart.insert_one({'order_id': self.order_id, 'order_user': self.order_user, 'creation_time': self.creation_time,
                         'prefer_delivery_time': self.prefer_delivery_time, 'actual_delivery_time': self.actual_delivery_time,
                         'status': self.status, 'text': self.text, 'address': self.address, 'composition': self.composition})
        return 'The record was created successfully'

    def order_change_status(self, status):
        order_data = cart.find_one_and_update(filter={'order_id': self.order_id}, update={'$set': {'status': status}})
        if order_data is None:
            return f'No records with this order_id:{self.order_id} were found'

    def order_set_actual_delivery_time(self, time):
        order_data = cart.find_one_and_update(filter={'order_id': self.order_id}, update={'$set': {'actual_delivery_time': time}})
        if order_data is None:
            return f'No records with this order_id:{self.order_id} were found'

