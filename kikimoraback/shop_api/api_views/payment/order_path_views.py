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
from shop_api.serializers import OrderPathSerializer
from shop_api.services import (
    CheckCartService,
    DeliveryService,
    PaymentService,
    UserIdentifierService,
)

load_dotenv()
logger = logging.getLogger("shop")
logger.setLevel(logging.DEBUG)


class OrderPath(APIView):

    def post(self, request) -> Response:
        serializer = OrderPathSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        cart_service = Cart()
        check_cart_service = CheckCartService(cart_service)
        order_service = Order()
        payment_service = PaymentService(cart_service, order_service)

        user = request.user
        logger.debug(f"Данные полученные на вход orderpath:\n{validated_data}")

        steps = validated_data["steps"]
        cart = validated_data.get("cart")
        bonuses = validated_data.get("usedBonus")
        user_data = validated_data.get("userData")
        delivery_data = validated_data.get("deliveryData")
        comment = validated_data.get("comment")

        if not steps:
            logger.error(
                "В OrderPath пришел запрос не содержащий steps.\n"
                f"request.data: {data}\n"
                f"user: {user}"
            )
            return Response(
                {"error": "Невозможно обработать пустой запрос."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not cart_service.ping():
            return Response(
                {"error": "Не удалось подключиться к сервису работы корзины."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        if not order_service.ping():
            return Response(
                {"error": "Не удалось оформить заказ. Повторите попытку позже."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        logger.debug(f"cookie from user:{request.COOKIES}")
        user_id_service = UserIdentifierService(request)
        user_id, cookie_response = user_id_service.get_or_create_user_id()
        if not user_id:
            logger.debug(
                "Неудалось опознать пользователя\n"
                f"cookie_response:{user_response}\n"
                f"user_id:{user_id}"
            )
            return cookie_response

        # Если запрошена оплата — выполнить все шаги
        if "payment_step" in steps:
            steps = ["check_cart_step", "delivery_step", "payment_step"]

        def check_cart_step(user_id, cart, check_cart_service):
            response = check_cart_service.check(user_id, cart)
            if response.data.get("price_mismatches") or response.data.get(
                "deleted_products"
            ):
                return response, True
            return response, False

        step_actions = {
            "check_cart_step": lambda: check_cart_step(
                user_id, cart, check_cart_service
            ),
            "delivery_step": lambda: (
                DeliveryService(cart_service).calculate(
                    user_id=user_id,
                    user_data=user_data,
                    delivery_data=delivery_data,
                    comment=comment,
                    steps=steps,
                ),
                False,
            ),
            "payment_step": lambda: (
                payment_service.process_payment(
                    user_id=user_id,
                    user_data=user_data,
                    bonuses=bonuses,
                ),
                False,
            ),
        }

        last_response = Response()

        for step in steps:
            logger.debug(f"Текущий шаг в orderpath:{step}")
            action = step_actions.get(step)
            if action:
                response, should_stop = action()
                last_response = response
                if should_stop or response.status_code >= 400:
                    return response
        if cookie_response:
            last_response.set_cookie(
                key=cookie_response["key"],
                value=cookie_response["value"],
                **cookie_response["options"],
            )
        return last_response
