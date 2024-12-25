from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from collections import defaultdict
from pymongo import ASCENDING
import asyncio
import os
from dotenv import load_dotenv
import logging
from ..caches import active_products_cash, get_limit_product_cash, get_discount_cash
from ..models import Product, Subcategory
load_dotenv()
logger = logging.getLogger('shop')


class Cart:
    db_client = None

    def __init__(self, db_client=None):
        if Cart.db_client is None:
            Cart.db_client = db_client
        self.cart_collection = Cart.db_client["kikimora"]["cart"]

    async def get_cart_data(self, user_id):
        return await self.cart_collection.find_one({"customer": user_id})

    async def create_cart(self, user_id, front_cart_data):
        if not await self.get_cart_data(user_id):
            self.cart_collection.insert_one({"customer": user_id,
                                             "products": front_cart_data['products'],
                                             "total": front_cart_data['total']})
        else:
            logger.warning(f"Пользователь с id {user_id}, уже находиться в mongodb['cart'].")

    async def cync_cart_data(self, user_id, front_cart_data):
        back_user_data = await self.get_cart_data(user_id)
        if front_cart_data:
            if not back_user_data:
                await self.create_cart(user_id, front_cart_data)
                return
            else:
                self.cart_collection.update_one({"customer": user_id},
                                                {"$set": {
                                                    "products": front_cart_data['products'],
                                                    "total": front_cart_data['total']
                                                }})
                return
        else:
            if back_user_data:
                logger.info(f'Данные для корзины пользователя с id {user_id} загружены из mongo_db.')
                return True, back_user_data
            else:
                return

    async def check_cart_data(self, front_data, user_id):
        deleted_products = []
        price_mismatches = []
        total_db = 0
        minus_double_check_price = defaultdict(float)
        updated_cart = {'products': []}

        if not front_data:
            logger.warning(f'Корзина пользователя с id {user_id} пришла пустой от frontend.')
            return None

        # Кэшируем скидки и товары
        active_discounts = get_discount_cash().filter(active=True, start__lte=timezone.now(), end__gte=timezone.now())
        product_ids = [product['product_id'] for product in front_data['product']]
        product_db_data = active_products_cash().filter(product_id__in=product_ids)

        # Пройдем по всем товарам в корзине
        for product in front_data['product']:
            product_data = next((item for item in product_db_data if item['product_id'] == product['product_id']), None)

            if not product_data:
                # Товар удалён из базы
                deleted_products.append(product['name'])
                continue

            # Ищем скидку: сначала для подкатегории, затем индивидуальную
            discount = active_discounts.filter(subcategory__in=product_data['subcategory']).first()
            product_discount = active_discounts.filter(product_id=product['product_id']).first()
            if product_discount:
                discount = product_discount

            # Рассчитываем актуальную цену с учётом скидки
            price = product_data['price']
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

    async def create_indexes(self):
        await self.cart_collection.create_index([("customer", ASCENDING)])


client = AsyncIOMotorClient(os.getenv("MONGOCON"))


async def main():
    client = AsyncIOMotorClient(os.getenv("MONGOCON"))
    try:
        client.admin.command('ping')
        logger.info("Успешное подключение к БД.")
    except Exception as e:
        logger.critical("Не удалось подключиться к MONGO")
        return
    cart = Cart(client)
    await cart.create_indexes()

    # Добавляем товар в корзину
    result = await cart.add_item(1, "item_123", add=2)
    print(result)


asyncio.run(main())