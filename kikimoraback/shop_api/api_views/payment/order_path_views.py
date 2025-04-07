import json
import logging
import os
import uuid

from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

import requests
from celery.result import AsyncResult
from dotenv import load_dotenv

from shop.API.yookassa_api import PaymentYookassa
from shop.MongoIntegration.Cart import Cart
from shop.MongoIntegration.Order import Order
from shop.services.caches import *

from shop_api.services.authentication import CookieJWTAuthentication

load_dotenv()
logger = logging.getLogger("shop")
logger.setLevel(logging.DEBUG)

load_dotenv()
logger = logging.getLogger("shop")
logger.setLevel(logging.DEBUG)


class OrderPath(APIView):

    def post(self, request) -> Response:
        # Инициализация сервисов
        cart_service = Cart()
        order_service = Order()

        # Все возможные шаги
        all_steps = [
            "delivery_step",
            "check_cart_step",
            "promo_code_step",
            "payment_step",
        ]

        # Данные из запроса
        user = request.user
        data = request.data
        steps = data.get("steps", [])
        delivery_data = data.get("deliveryData", {})
        cart = data.get("cart")
        bonuses = data.get("usedBonus")
        user_data = data.get("userData")
        delivery_data = data.get("deliveryData")
        comment = request.data.get("comment")
        # Проверка входных данных
        if not steps:
            logger.error(
                "В OrderPath пришел запрос не содержащий steps.\n"
                f"request.data: {data}\n"
                f"user: {user}"
            )
            return Response(
                {"error": "Невозможно обработать пустой запрос."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Проверка доступности сервисов
        if not cart_service.ping():
            return Response(
                {
                    "error": "Не удалось подключиться к сервису работы корзины. Перезагрузите страницу."
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if not order_service.ping():
            return Response(
                {"error": "Не удалось оформить заказ. Повторите попытку позже"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # Определение user_id
        if "payment_step" in steps:
            steps = all_steps

        response = Response()
        if not isinstance(user, AnonymousUser):
            try:
                user_id = CustomUser.objects.get(user_id=user.user_id).user_id
            except CustomUser.DoesNotExist:
                return Response(
                    {"error": "Пользователь не найден."},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            user_id = request.COOKIES.get("user_id", None)
            if not user_id:
                user_id = str(uuid.uuid4())
                response.set_cookie(
                    "user_id",
                    user_id,
                    max_age=60 * 60 * 24 * 30,
                    httponly=True,
                    secure=True,
                )

        # Функция расчета доставки через Яндекс API
        def yandex_calculation(
            user_id: int | str, delivery_data: dict, response: Response
        ) -> Response:
            MAX_RANGE = 5000  # Максимальное расстояние для первого тарифа
            ADD_COST = 100  # Дополнительная стоимость за каждый диапазон

            token = os.getenv("YANDEX_TOKEN")
            headers = {"Authorization": f"Bearer {token}", "Accept-Language": "ru/ru"}
            address = delivery_data.get("address")  # Получаем адрес из delivery_data

            if not address:
                response.status_code = status.HTTP_400_BAD_REQUEST
                response.data = {"error": "Не передан адрес для расчета доставки."}
                return response

            payload = {
                "route_points": [
                    {"fullname": "Санкт-Петербург, 11-я Красноармейская улица, 11"},
                    {"fullname": f"Санкт-Петербург, {address}"},
                ]
            }

            try:
                yandex_response = requests.post(
                    "https://b2b.taxi.yandex.net/b2b/cargo/integration/v2/check-price",
                    headers=headers,
                    json=payload,
                )
            except requests.RequestException as e:
                logger.critical(f"Ошибка при попытке отправить запрос к API Яндекс:{e}")
                response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
                response.data = {
                    "error": "Ошибка при попытке расчета стоимости. "
                    "Попробуйте оформить заказ позже или обратитесь в магазин."
                }
                return response

            try:
                yandex_data = yandex_response.json()
            except ValueError:
                logger.error(
                    f"Некорректный JSON в ответе от API Яндекс. Статус: {yandex_response.status_code}"
                )
                response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
                response.data = {
                    "error": "Сервис доставки временно недоступен. Перезагрузите страницу и попробуйте ещё раз."
                }
                return response

            default_error_msg = "Сейчас сервис доставки недоступен. Вы можете оформить доставку самостоятельно или обратиться в магазин."

            if yandex_response.ok:
                distance_meters = yandex_data["distance_meters"]
                price = round(float(yandex_data["price"]))

                # Увеличиваем стоимость в зависимости от расстояния
                if distance_meters <= MAX_RANGE:
                    price += ADD_COST
                elif distance_meters > MAX_RANGE and distance_meters <= MAX_RANGE * 2:
                    price += ADD_COST * 2
                else:
                    price += ADD_COST * 3

                response.status_code = status.HTTP_200_OK
                response.data = {"price": price, "distance_meters": distance_meters}
                return response

            elif yandex_response.status_code == 400:
                logger.error(
                    f"Ошибка во время расчета стоимости заказа.\nAddress:{address}\n ERROR:{yandex_data}"
                )
                response.status_code = status.HTTP_400_BAD_REQUEST
                response.data = {
                    "error": "Не удалось рассчитать стоимость доставки. "
                    "Проверьте правильность введенного адреса."
                }
                return response

            elif yandex_response.status_code == 401:
                logger.critical("Передан неверный токен yandex-delivery.")
                response.status_code = status.HTTP_401_UNAUTHORIZED
                response.data = {"error": default_error_msg}
                return response

            else:
                logger.error(
                    f"Непредвиденная ошибка во время расчета стоимости заказа.\nAddress:{address}\n ERROR:{yandex_data}"
                )
                response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
                response.data = {"error": default_error_msg}
                return response

        def check_cart(
            user_id: int | str, cart_data: dict, response: Response
        ) -> Response:
            if not cart_data:
                response.status = status.HTTP_400_BAD_REQUEST
                response.data = {"error": "В корзине ничего нет"}
                return response
            card_updated = cart_service.check_cart_data(
                front_data=cart_data, user_id=user_id
            )
            cart_service.sync_cart_data(
                user_id=user_id,
                front_cart_data={
                    "total": card_updated["total"],
                    "products": card_updated["updated_cart"]["products"],
                    "add_bonuses": card_updated["add_bonuses"],
                },
            )
            response.status = status.HTTP_200_OK
            response.data = card_updated
            return response

        def payment(
            user, user_data, bonuses, comment, delivery_data, response: Response
        ) -> Response:
            cart_service.add_delivery(user, delivery_data, user_data, comment)
            cart_data = cart_service.get_cart_data(user)
            delivery_data = cart_data["delivery_data"]
            order_number = order_service.get_neworder_num(user_id)
            payment_service = PaymentYookassa()
            if bonuses:
                try:
                    UserBonusSystem.deduct_bonuses(user_id=user_id, bonuses=bonuses)
                except Exception as e:
                    logger.error(
                        f"Неудалось списать бонусы с баланса пользователя id {user_id}. Ошибка: {e}"
                    )
                    response.status_code = status.HTTP_400_BAD_REQUEST
                    response.data.error = "Неудалось списать бонусы в счёт заказа."
                    return response

            response = json.loads(
                payment_service.send_payment_request(
                    user_data=user_data,
                    cart=cart_data,
                    order_id=order_number,
                    delivery_data=delivery_data,
                    bonuses=bonuses,
                )
            )

            if not response:
                return Response(
                    {
                        "error": "Во время оформления заказа произошла ошибка.\n"
                        "Попробуйте перезагрузить страниц."
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )
            cart_service.add_payment_data(
                user_id=user_id,
                payment_id=response["id"],
                order_number=order_number,
                bonuses=bonuses,
            )
            order_service.create_order_on_cart(
                cart_service.get_cart_data(user_id=user_id)
            )
            cart_service.delete_cart(user_id=user_id)
            return Response(
                {
                    "detail": "Redirecting to payment",
                    "redirect_url": response["confirmation"]["confirmation_url"],
                },
                status=status.HTTP_302_FOUND,
            )

        if not steps:
            return Response(
                {"error": "Шаг не определен."}, status=status.HTTP_400_BAD_REQUEST
            )

        if "delivery_step" in steps:
            response = yandex_calculation(user_id, delivery_data, response)
            delivery_data["deliveryCost"] = response.data["price"]
            if response.data.get("error", None):
                return response
        if "check_cart_step" in steps:
            response = check_cart(user_id, cart, response)
            if response.data["price_mismatches"]:
                return response
            elif response.data["deleted_products"]:
                return response
        if "payment_step" in steps:
            response = payment(
                user_id, user_data, bonuses, comment, delivery_data, response
            )

        return response
