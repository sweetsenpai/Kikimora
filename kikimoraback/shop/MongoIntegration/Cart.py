from pymongo import MongoClient, ASCENDING
from collections import defaultdict
from datetime import datetime
import logging
from ..caches import active_products_cash, get_limit_product_cash, get_discount_cash, get_promo_cash
from ..models import Product, Subcategory
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
                                                    "total": front_cart_data['total']
                                                }})
                return self.get_cart_data(user_id)
        else:
            if back_user_data:
                logger.info(f'Данные для корзины пользователя с id {user_id} загружены из mongo_db.')
                return self.get_cart_data(user_id)
            else:
                return None

    def check_cart_data(self, front_data, user_id):
        deleted_products = []
        price_mismatches = []
        total_db = 0
        minus_double_check_price = defaultdict(float)
        updated_cart = {'products': []}

        if not front_data:
            logger.warning(f'Корзина пользователя с id {user_id} пришла пустой от frontend.')
            return None

        # Кэшируем скидки и товары
        active_discounts = get_discount_cash()
        limit_products = get_limit_product_cash()
        product_ids = [product['product_id'] for product in front_data['products']]

        product_db_data = active_products_cash().filter(product_id__in=product_ids)

        # Пройдем по всем товарам в корзине
        for product in front_data['products']:
            product_data = next((item for item in product_db_data if item.product_id == product['product_id']), None)

            if not product_data:
                # Товар удалён из базы
                deleted_products.append(product['name'])
                continue
            limit_product = limit_products.filter(product_id=product['product_id']).first()
            if limit_product:
                price = limit_product.price
            # Ищем скидку: сначала для подкатегории, затем индивидуальную
            else:
                discount = active_discounts.filter(subcategory__in=product_data.subcategory.all()).first()
                product_discount = active_discounts.filter(product_id=product['product_id']).first()
                price = product_data.price
                if product_discount:
                    discount = product_discount

                    # Рассчитываем актуальную цену с учётом скидок
                if discount:
                    if discount.discount_type == 'percentage':
                        price -= price * (discount.value / 100)
                    else:
                        price -= discount.value

            # Сравниваем цену с переданной от фронтенда
            if price != product['price']:
                price_mismatches.append({
                    'product_id': product['product_id'],
                    'name': product['name'],
                    'old_price': product['price'],
                    'new_price': price,
                })

            # Добавляем товар в обновлённую корзину
            updated_cart['products'].append({
                'product_id': product['product_id'],
                'name': product['name'],
                'price': price,
                'quantity': product['quantity'],
            })

            # Учитываем цену в итоговой сумме
            total_db += price * product['quantity']
            minus_double_check_price[product['product_id']] = price * product['quantity']
        # Проверяем итоговую сумму
        if total_db != front_data['total']:
            logger.warning(
                f'Итоговая сумма не совпадает. Пересчитанная сумма: {total_db}, переданная сумма: {front_data["total"]}.'
            )

        return {
            'total': total_db,
            'deleted_products': deleted_products,
            'price_mismatches': price_mismatches,
            'updated_cart': updated_cart,
        }

    def add_delivery(self, user_id, delivery_data, customer_data, comment):
        if delivery_data['deliveryMethod']== 'Доставка':
            self.cart_collection.update_one({"customer": user_id},
                                            {"$set": {
                                                "delivery_data.method": "Доставка",
                                                "delivery_data.street": delivery_data['street'],
                                                "delivery_data.building": delivery_data['houseNumber'],
                                                "delivery_data.apartment": delivery_data.get('apartment'),
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

    def apply_promo(self, promo, user_id):
        promo_data = get_promo_cash().objects.filter(code=promo)
        cart = self.get_cart_data(user_id)
        if not promo_data:
            return None
        if promo_data.type == 'delivery':
            return {'delivery_free': True}
        if promo.promo_product in cart['products']:
            ...
        if not promo_data.min_sum:
            ...

    def add_payement_data(self, payment_id, user_id, order_number):
        self.cart_collection.update_one({"customer": user_id}, {'$set': {'payment_id': payment_id,
                                                                         'order_number': order_number}})

    def remove_payement_id(self, payment_id, user_id):
        self.cart_collection.update_one({"customer": user_id}, {'$unset': {'payment_id': payment_id}})
        
    def delete_cart(self, user_id=None, payment_id=None):
        if payment_id:
            self.cart_collection.delete_one({"payment_id": payment_id})
        else:
            self.cart_collection.delete_one({"customer": user_id})

    def create_indexes(self):
        self.cart_collection.create_index([("customer", ASCENDING)])
