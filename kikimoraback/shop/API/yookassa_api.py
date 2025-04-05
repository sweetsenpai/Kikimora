import logging
import os
from decimal import ROUND_HALF_UP, Decimal
from pprint import pprint

from dotenv import load_dotenv
from yookassa import Configuration, Payment, Receipt

load_dotenv()

logger = logging.getLogger("shop")
logger.setLevel(logging.DEBUG)

key = "test__kXJEEjyiSkZNQzUGm5nb5EwNtgjz4HHAIBXojqhYMU"
id = "1007767"


class PaymentYookassa:
    def __init__(self):
        Configuration.configure(os.getenv("YOOMONEY_ID_2"), os.getenv("YOOMONEY_KEY_2"))

    def item_check_builder(self, cart: dict, delivery_data: dict, bonuses) -> list:
        """
        Создает список товаров и доставки для отправки на оплату.

        Args:
            cart (dict): Словарь с данными корзины. Ожидает ключи:
                - products (list): список товаров с полями 'name', 'price', 'quantity'.
                - total (float|Decimal): общая стоимость корзины.
            delivery_data (dict): Данные о доставке. Ожидает ключи:
                - deliveryMethod (str): способ доставки.
                - cost (float|Decimal): стоимость доставки.
            bonuses (float|Decimal): Количество бонусов для списания.

        Returns:
            list: Список товаров и услуги доставки в формате для оплаты.
        """

        bonuses = Decimal(bonuses or 0)

        items = []

        cart_total = Decimal(cart["total"])

        def create_item(product: dict, bonus, quantity=None) -> dict:
            """Создаем словари товара для вставки в счет на оплату"""
            item = {
                "description": product["name"],
                "quantity": quantity if quantity else product["quantity"],
                "amount": {
                    "value": float(
                        (Decimal(product["price"]) - bonus).quantize(
                            Decimal("0.01"), rounding=ROUND_HALF_UP
                        )
                    ),
                    "currency": "RUB",
                },
                "vat_code": "1",
                "payment_mode": "prepayment",
                "payment_subject": "commodity",
                "country_of_origin_code": "RU",
                "measure": "piece",
            }
            return item

        # Находим товар с самой большой стоимостью,
        # чтобы потом попытаться погасить все балы из его цены,
        # вместо распределения баллов по всему чеку
        max_price_product = max(cart["products"], key=lambda x: x["price"])

        if max_price_product["price"] - int(bonuses) >= 1 and bonuses > 0:
            # Списываем бонусы с этого товара
            items.append(create_item(max_price_product, bonuses, 1))
            # Если колличество товара с которого можно за раз списать все баллы больше 1,
            # То мы первый товар добавляем в чек с измененой ценой,
            # а оставшиеся его экземпляры добавляем как обычные товары
            if max_price_product["quantity"] > 1:
                items.append(
                    create_item(max_price_product, 0, max_price_product["quantity"] - 1)
                )
            # Добавляем остальные товары без учета бонусов
            for product in cart["products"]:
                if product != max_price_product:
                    items.append(create_item(product, 0))
        else:
            # Распределяем бонусы по всем товарам
            remaining_bonuses = bonuses
            last_product = cart["products"][-1]
            for product in cart["products"]:
                product_price = Decimal(product["price"])
                if product != last_product:
                    bonus_for_product = (product_price / cart_total * bonuses).quantize(
                        Decimal("0.01"), rounding=ROUND_HALF_UP
                    )
                    remaining_bonuses -= bonus_for_product
                    items.append(create_item(product, bonus_for_product))
                else:
                    # Для последнего товара распределяем бонусы равномерно,
                    # чтобы избежать ошибки когда при большом числе товаров
                    # цена товара становиться отрицательной
                    items.append(
                        create_item(product, remaining_bonuses / product["quantity"])
                    )
        # Добавляем доставку
        items.append(
            {
                "description": delivery_data["method"],
                "quantity": 1,
                "amount": {"value": delivery_data["cost"], "currency": "RUB"},
                "vat_code": "1",
                "payment_mode": "prepayment",
                "payment_subject": "service",
            }
        )

        return items

    def send_payment_request(self, user_data, cart, order_id, delivery_data, bonuses):
        bonuses = bonuses or 0
        recipient_data = {
            "amount": {"value": cart["total"] - bonuses, "currency": "RUB"},
            "confirmation": {
                "type": "redirect",
                "return_url": os.getenv("PAYMENT_BACK_URL"),
            },
            "capture": True,
            "description": f"Оплата №{order_id} для {user_data['phone']}",
            "receipt": {
                "customer": {
                    "full_name": user_data["fio"],
                    "email": user_data["email"],
                    "phone": user_data["phone"],
                },
                "items": self.item_check_builder(cart, delivery_data, bonuses),
            },
        }
        try:
            payement = Payment.create(recipient_data)
        except Exception as e:
            logger.error(
                f"Во время формирования платежа произошла ошибка на уровне загрузки данных в юкасу.\n"
                f"Данные для чека:{recipient_data}\n"
                f"ERROR:{e}"
            )
            return False
        try:
            logger.info(f"Платеж {order_id} успешно создан.")
            return payement.json()
        except KeyError as e:
            logger.error(f"Ошибка при извлечении данных из ответа yookassa: {e}")
        except Exception as e:
            logger.critical(
                f"Не удалось создать оплату для клиента. \nДанные корзины:{cart}"
                f"\nЧЕК:{recipient_data}"
                f"\nОШИБКА: {e}"
            )
        return False
