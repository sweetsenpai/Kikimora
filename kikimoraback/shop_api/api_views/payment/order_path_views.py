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
from shop_api.services.order_path_services.check_cart_service import CheckCartService
from shop_api.services.order_path_services.delivery_service import DeliveryService
from shop_api.services.order_path_services.payment_service import PaymentService

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
        check_cart_service = CheckCartService(cart_service)
        order_service = Order()
        payment_service = PaymentService(cart_service, order_service)

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

        if not steps:
            return Response(
                {"error": "Шаг не определен."}, status=status.HTTP_400_BAD_REQUEST
            )

        if "delivery_step" in steps:
            delivery_sertsvice = DeliveryService()
            response = delivery_sertsvice.calculate(user_id, delivery_data)
        if "check_cart_step" in steps:
            response = check_cart_service.check(user_id, cart)

            if response.data.get("price_mismatches"):
                return response
            elif response.data.get("deleted_products"):
                return response
        if "payment_step" in steps:
            response = payment_service.process_payment(
                user_id=user_id,
                user_data=user_data,
                bonuses=bonuses,
                comment=comment,
                delivery_data=delivery_data,
            )

        return response
