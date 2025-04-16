import json
import logging

from rest_framework import status
from rest_framework.response import Response

from shop.API.yookassa_api import PaymentYookassa
from shop.MongoIntegration.Cart import Cart
from shop.MongoIntegration.Order import Order
from shop.services.caches import UserBonusSystem

logger = logging.getLogger("shop")

class PaymentService:
    def __init__(self, cart_service=None, order_service=None, payment_gateway=None):
        self.cart_service = cart_service or Cart()
        self.order_service = order_service or Order()
        self.payment_gateway = payment_gateway or PaymentYookassa()

    def process_payment(
        self, user_id, user_data, bonuses, comment, delivery_data
    ) -> Response:
        try:
            self.cart_service.add_delivery(user_id, delivery_data, user_data, comment)
            cart_data = self.cart_service.get_cart_data(user_id)
            delivery_data = cart_data.get("delivery_data")
            order_number = self.order_service.get_neworder_num(user_id)

            if bonuses:
                try:
                    UserBonusSystem.deduct_bonuses(user_id=user_id, bonuses=bonuses)
                except Exception as e:
                    logger.error(
                        f"Не удалось списать бонусы с баланса пользователя id {user_id}. Ошибка: {e}"
                    )
                    return Response(
                        {"error": "Не удалось списать бонусы в счёт заказа."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            response_data = json.loads(
                self.payment_gateway.send_payment_request(
                    user_data=user_data,
                    cart=cart_data,
                    order_id=order_number,
                    delivery_data=delivery_data,
                    bonuses=bonuses,
                )
            )

            if not response_data:
                return Response(
                    {
                        "error": "Во время оформления заказа произошла ошибка. "
                                 "Попробуйте перезагрузить страницу."
                    },
                    status=status.HTTP_503_SERVICE_UNAVAILABLE,
                )

            self.cart_service.add_payment_data(
                user_id=user_id,
                payment_id=response_data["id"],
                order_number=order_number,
                bonuses=bonuses,
            )

            self.order_service.create_order_on_cart(cart_data)
            self.cart_service.delete_cart(user_id=user_id)

            return Response(
                {
                    "detail": "Redirecting to payment",
                    "redirect_url": response_data["confirmation"]["confirmation_url"],
                },
                status=status.HTTP_302_FOUND,
            )

        except Exception as e:
            logger.exception(f"Ошибка в процессе оплаты: {e}")
            return Response(
                {"error": "Не удалось обработать оплату."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
