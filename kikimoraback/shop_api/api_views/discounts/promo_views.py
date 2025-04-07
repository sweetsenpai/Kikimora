from rest_framework.response import Response

from shop.models import PromoSystem
from shop.MongoIntegration.Cart import Cart


class PromoCode(APIView):
    def post(self, request):
        user = request.user
        cart_service = Cart()
        cart_data = cart_service.get_cart_data(user_id=user.user_id)
        promo_code = request.data.get("promoCode")
        promo = (
            PromoSystem.objects.filter(code=promo_code, active=True)
            .prefetch_related("promocodeuseg_set")
            .first()
        )
        try:
            response = self.apply_promo(cart_data, promo, user, promo_code)
        except Exception as error:
            logger.error(
                f"Ошибка применения промокода.\nPROMO: {promo}\nCART: {cart_data}\nERROR: {error}"
            )
            return Response(
                {
                    "error": "Сейчас невозможно использовать этот промокод. Попробуйте позже."
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return response

    def apply_promo(self, cart_data, promo, user, promo_code):
        if not promo:
            return Response(
                {"error": "Промокод не существует."}, status=status.HTTP_404_NOT_FOUND
            )

        if promo.one_time and not isinstance(user, AnonymousUser):
            return Response(
                {
                    "error": f"Зарегистрируйтесь или войдите в аккаунт, чтобы использовать промокод {promo_code}."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if (
            promo.one_time
            and promo.promocodeuseg_set.filter(user_id=user.user_id).exists()
        ):
            return Response(
                {"error": "Промокод уже использован."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if promo.min_sum and promo.min_sum > cart_data["total"]:
            return Response(
                {
                    "error": f"Минимальная стоимость заказа для использования промокода {promo.min_sum} р."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        promo_metadata = {"promocode_id": promo.promo_id, "one_time": promo.one_time}

        if promo.type == "delivery":
            return self.apply_delivery_discount(cart_data, promo, promo_metadata)

        if promo.amount:
            return self.apply_fixed_discount(cart_data, promo, promo_metadata)

        return self.apply_percentage_discount(cart_data, promo, promo_metadata)

    def apply_delivery_discount(self, cart_data, promo, promo_metadata):
        try:
            if cart_data["delivery_data"]["method"] != "Доставка":
                return Response(
                    {
                        "error": "Невозможно применить промокод для бесплатной доставки в заказе без доставки."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except KeyError:
            return Response(
                {
                    "error": "Невозможно применить промокод для бесплатной доставки в заказе без доставки."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        promo_metadata["type"] = "delivery"
        promo_metadata["new_total"] = (
            cart_data["total"] - cart_data["delivery_data"]["cost"]
        )
        Cart().apply_promo(cart_data["customer"], promo_metadata)
        return Response(status=status.HTTP_200_OK, data={"freeDelivery": True})

    def apply_fixed_discount(self, cart_data, promo, promo_metadata):
        total_after_discount = cart_data["total"] - promo.amount
        if total_after_discount < 1:
            return Response(
                {
                    "error": f"Нельзя применить промокод, недостаточная сумма заказа. Минимальная сумма заказа {promo.min_sum} р."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        promo_metadata["type"] = "fixed"
        promo_metadata["new_total"] = total_after_discount
        promo_metadata["discount_value"] = promo.amount

        Cart().apply_promo(cart_data["customer"], promo_metadata)
        return Response(data={"amount": promo.amount}, status=status.HTTP_200_OK)

    def apply_percentage_discount(self, cart_data, promo, promo_metadata):
        discount_value = round(cart_data["total"] * (promo.procentage * 0.01))
        new_total = cart_data["total"] - discount_value

        promo_metadata["type"] = "percentage"
        promo_metadata["new_total"] = new_total
        promo_metadata["discount_value"] = promo.procentage
        Cart().apply_promo(cart_data["customer"], promo_metadata)
        return Response(
            data={"percentage": promo.procentage}, status=status.HTTP_200_OK
        )
