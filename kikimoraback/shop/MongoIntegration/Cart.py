from pymongo import MongoClient, ASCENDING
from ..MongoIntegration.db_connection import MongoDBClient
from collections import defaultdict
from datetime import datetime
import logging
from ..caches import active_products_cash, \
                    get_limit_product_cash, \
                    get_discount_cash, user_bonus_cash
from ..models import Product, Subcategory
from ..tasks import update_price_cache
from ..serializers import ProductSerializer
import json
logger = logging.getLogger('shop')


class Cart:
    def __init__(self):
        self.db_client = MongoDBClient.get_client()
        self.cart_collection = self.db_client["kikimora"]["cart"]
            
    def ping(self):
        try:
            self.db_client.admin.command('ping')
            return True
        except Exception as e:
            logger.critical(f"Не удалось подключиться к mongodb.\n Errpr:{e}")
            return False

    def get_cart_data(self, user_id=None, payment_id=None):
        """Получить информацию о корзине клиента по его id или с помощью payment_id"""
        if payment_id:
            return self.cart_collection.find_one({"payment_id": payment_id})
        return self.cart_collection.find_one({"customer": user_id})

    def create_cart(self, user_id, front_cart_data):
        if not self.get_cart_data(user_id):
            self.cart_collection.insert_one({"customer": user_id,
                                             "products": front_cart_data['products'],
                                             "total": front_cart_data['total']})
        else:
            logger.warning(f"Пользователь с id {user_id}, уже находится в mongodb['cart'].")

    def add_unregistered_mark(self, user_id):
        self.cart_collection.update_one({"customer": user_id}, {'$set': {'unregistered': True}})

    def sync_cart_data(self, user_id, front_cart_data):
        back_user_data = self.get_cart_data(user_id)
        if front_cart_data:
            if not back_user_data:
                self.create_cart(user_id, front_cart_data)
                return self.get_cart_data(user_id)
            else:
                self.cart_collection.update_one({"customer": user_id},
                                                {"$set": {
                                                    "products": front_cart_data['products'],
                                                    "total": front_cart_data['total'],
                                                    "add_bonuses": front_cart_data['add_bonuses']
                                                }})
                return self.get_cart_data(user_id)
        else:
            if back_user_data:
                logger.info(f'Данные для корзины пользователя с id {user_id} загружены из mongo_db.')
                return self.get_cart_data(user_id)
            else:
                return None

    def check_cart_data(self, front_data, user_id):
        """
        Проверяет данные корзины, переданные от фронтенда, и возвращает актуальные данные.

        Args:
            front_data (dict): Данные корзины от фронтенда.
            user_id (int): ID пользователя.

        Returns:
            dict: Словарь с актуальными данными корзины.
        """
        deleted_products = []
        price_mismatches = []
        total_db = 0
        bonuses_to_add = 0
        updated_cart = {'products': []}

        if not front_data:
            logger.warning(f'Корзина пользователя с id {user_id} пришла пустой от фронтенда.')
            return None

        # Получаем кэшированные данные о ценах, скидках и фотографиях
        cached_data = update_price_cache()
        product_cash = active_products_cash()
        price_map = cached_data['price_map']
        # Пройдем по всем товарам в корзине
        for product in front_data['products']:
            product_id = product['product_id']

            # Проверяем, есть ли товар в кэше
            if product_id not in price_map:
                deleted_products.append(product['name'])
                continue

            # Получаем актуальную цену и бонусы из кэша
            final_price = price_map[product_id]
            product_bonus = product_cash.get(product_id=product['product_id']).bonus
            bonuses_to_add += product_bonus * product['quantity']

            # Сравниваем цену с переданной от фронтенда
            if final_price != product['price']:
                price_mismatches.append({
                    'product_id': product_id,
                    'name': product['name'],
                    'old_price': product['price'],
                    'new_price': final_price,
                })

            # Обновляем данные корзины
            updated_cart['products'].append({
                'product_id': product_id,
                'name': product['name'],
                'price': final_price,
                'bonus': product_bonus,
                'quantity': product['quantity'],
            })

            # Считаем общую сумму
            total_db += final_price * product['quantity']

        # Проверяем, совпадает ли итоговая сумма
        if total_db != front_data['total']:
            logger.warning(
                f'Итоговая сумма не совпадает. Пересчитанная сумма: {total_db}, переданная сумма: {front_data["total"]}.'
            )

        return {
            'total': total_db,
            'deleted_products': deleted_products,
            'price_mismatches': price_mismatches,
            'updated_cart': updated_cart,
            'add_bonuses': bonuses_to_add
        }

    def add_delivery(self, user_id, delivery_data, customer_data, comment):
        if delivery_data['deliveryMethod']== 'Доставка':
            self.cart_collection.update_one({"customer": user_id},
                                            {"$set": {
                                                "delivery_data.method": "Доставка",
                                                "delivery_data.street": delivery_data['street'],
                                                "delivery_data.building": delivery_data['houseNumber'],
                                                "delivery_data.apartment": delivery_data['appartmentNumber'],
                                                "delivery_data.date":  datetime.strptime(delivery_data['date'], "%Y-%m-%d"),
                                                "delivery_data.time": delivery_data['time'],
                                                "delivery_data.cost":  delivery_data['deliveryCost'],

                                                "customer_data.fio": customer_data['fio'],
                                                "customer_data.phone": customer_data['phone'],
                                                "customer_data.email": customer_data['email'],

                                                "comment": comment,
                                                "date_of_creation": datetime.now()

                                            },
                                            "$inc": {
                                                "total": delivery_data['deliveryCost']
                                            },
                                             })
        else:
            self.cart_collection.update_one({"customer": user_id},
                                            {"$set": {
                                                "delivery_data.method": "Самовывоз",
                                                "delivery_data.date": datetime.strptime(delivery_data['date'], "%Y-%m-%d"),
                                                "delivery_data.time": delivery_data['time'],
                                                "delivery_data.cost": 0,

                                                "customer_data.fio": customer_data['fio'],
                                                "customer_data.phone": customer_data['phone'],
                                                "customer_data.email": customer_data['email'],

                                                "comment": comment,
                                                "date_of_creation": datetime.now()
                                            }
                                            })
            return

    def apply_promo(self, user_id, promo_data):
        print("____________________________________")
        print(promo_data)
        self.cart_collection.update_one({"customer": user_id},
                                        {"$set":
                                             {"promo_data.promo_id": promo_data['promocode_id'],
                                              "promo_data.type": promo_data['type'],
                                              "promo_data.one_time": promo_data['one_time'],
                                              "promo_data.value": promo_data.get('discount_value')}})
        return

    def add_payment_data(self, payment_id, user_id, order_number, bonuses):
        self.cart_collection.update_one({"customer": user_id}, {'$set': {'payment_id': payment_id,
                                                                         'order_number': order_number,
                                                                         'bonuses_deducted': bonuses}})

    def remove_payement_id(self, payment_id, user_id):
        self.cart_collection.update_one({"customer": user_id}, {'$unset': {'payment_id': payment_id}})
        
    def delete_cart(self, user_id=None, payment_id=None):
        if payment_id:
            self.cart_collection.delete_one({"payment_id": payment_id})
        else:
            self.cart_collection.delete_one({"customer": user_id})

    def create_indexes(self):
        self.cart_collection.create_index([("customer", ASCENDING)])
