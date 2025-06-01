import logging

from rest_framework import status
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class CheckCartService:
    def __init__(self, cart_service):
        self.cart_service = cart_service

    def check(self, user_id: int | str, cart_data: dict) -> Response:
        logger.debug(f"Данные пришли в CheckCartService:\n{cart_data}")
        if not cart_data:
            return Response({"error": "В корзине ничего нет"}, status=status.HTTP_400_BAD_REQUEST)

        card_updated = self.cart_service.check_cart_data(front_data=cart_data, user_id=user_id)

        self.cart_service.sync_cart_data(
            user_id=user_id,
            front_cart_data={
                "total": card_updated["total"],
                "products": card_updated["updated_cart"]["products"],
                "add_bonuses": card_updated["add_bonuses"],
            },
        )
        logger.debug("Ответ от сервиса проверки корзины:\n" f"data:\n{card_updated}")
        return Response(data=card_updated, status=status.HTTP_200_OK)
