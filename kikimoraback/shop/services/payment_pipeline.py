from rest_framework.response import Response
from rest_framework.views import APIView

class OrderPipeline(APIView):
    def post(self, request, *args, **kwargs):
        """
        Общий пайплайн для обработки заказа.
        Включает в себя:
        - Расчет стоимости доставки
        - Проверку корзины
        - Применение промокода
        - Оформление платежа
        """
        try:
            # Шаг 1: Расчет стоимости доставки
            delivery_data = self.calculate_delivery(request)
            if 'error' in delivery_data:
                return Response(delivery_data, status=status.HTTP_400_BAD_REQUEST)

            # Шаг 2: Проверка корзины
            cart_data = self.check_cart(request)
            if 'error' in cart_data:
                return Response(cart_data, status=status.HTTP_400_BAD_REQUEST)

            # Шаг 3: Применение промокода (если предоставлен)
            promo_code = request.data.get('promoCode')
            if promo_code:
                promo_response = self.apply_promo(request, cart_data)
                if 'error' in promo_response:
                    return Response(promo_response, status=status.HTTP_400_BAD_REQUEST)

            # Шаг 4: Оформление платежа
            payment_response = self.process_payment(request, cart_data, delivery_data)
            if 'error' in payment_response:
                return Response(payment_response, status=status.HTTP_400_BAD_REQUEST)

            # Если все успешно, возвращаем данные о заказе
            return Response({
                "delivery": delivery_data,
                "cart": cart_data,
                "payment": payment_response
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Ошибка при обработке заказа: {e}")
            return Response({"error": "Внутренняя ошибка сервера."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def calculate_delivery(self, request):
        """
        Выполняет расчет стоимости доставки через YandexCalculation.
        """
        address = request.data.get('address')
        if not address:
            return {"error": "Не передан адрес доставки."}

        yandex_calculation = YandexCalculation()
        response = yandex_calculation.post(request)
        if response.status_code != status.HTTP_200_OK:
            return {"error": response.data.get("error", "Ошибка расчета доставки.")}

        return response.data

    def check_cart(self, request):
        """
        Выполняет проверку корзины через CheckCart.
        """
        check_cart = CheckCart()
        response = check_cart.post(request)
        if response.status_code != status.HTTP_200_OK:
            return {"error": response.data.get("error", "Ошибка проверки корзины.")}

        return response.data

    def apply_promo(self, request, cart_data):
        """
        Применяет промокод через PromoCode.
        """
        promo_code_view = PromoCode()
        request._full_data = request.data.copy()  # Копируем данные запроса
        request._full_data['cart'] = cart_data  # Добавляем данные корзины в запрос
        response = promo_code_view.post(request)
        if response.status_code != status.HTTP_200_OK:
            return {"error": response.data.get("error", "Ошибка применения промокода.")}

        return response.data

    def process_payment(self, request, cart_data, delivery_data):
        """
        Выполняет оформление платежа через Payment.
        """
        payment_view = Payment()
        request._full_data = request.data.copy()  # Копируем данные запроса
        request._full_data['cart'] = cart_data  # Добавляем данные корзины в запрос
        request._full_data['delivery'] = delivery_data  # Добавляем данные доставки в запрос
        response = payment_view.post(request)
        if response.status_code != status.HTTP_302_FOUND:
            return {"error": response.data.get("error", "Ошибка оформления платежа.")}

        return response.data