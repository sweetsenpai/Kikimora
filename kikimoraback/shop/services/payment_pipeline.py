from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os
import requests
import uuid
import logging
from django.contrib.auth.models import AnonymousUser
from .models import CustomUser, PromoSystem, UserBonusSystem
from ..MongoIntegration.Cart import Cart
from ..MongoIntegration.Order import Order
from ..API.yookassa_api import PaymentYookassa

logger = logging.getLogger(__name__)


class OrderPipeline(APIView):

    def post(self, request):
        # Шаг 1: Расчет стоимости доставки
        delivery_response = self.calculate_delivery(request)
        if not delivery_response.get('success'):
            return Response(delivery_response, status=delivery_response.get('status', status.HTTP_400_BAD_REQUEST))

        # Шаг 2: Проверка корзины
        cart_response = self.check_cart(request)
        if not cart_response.get('success'):
            return Response(cart_response, status=cart_response.get('status', status.HTTP_400_BAD_REQUEST))

        # Шаг 3: Применение промокода (если есть)
        promo_code = request.data.get('promoCode')
        if promo_code:
            promo_response = self.apply_promo(request, promo_code)
            if not promo_response.get('success'):
                return Response(promo_response, status=promo_response.get('status', status.HTTP_400_BAD_REQUEST))

        # Шаг 4: Оплата
        payment_response = self.process_payment(request)
        if not payment_response.get('success'):
            return Response(payment_response, status=payment_response.get('status', status.HTTP_400_BAD_REQUEST))

        return Response({"detail": "Redirecting to payment", "redirect_url": payment_response['redirect_url']}, status=status.HTTP_302_FOUND)

    def calculate_delivery(self, request):
        token = os.getenv('YANDEX_TOKEN')
        headers = {"Authorization": f"Bearer {token}", 'Accept-Language': 'ru/ru'}
        address = request.data.get('address')
        if not address:
            logger.warning('Не передан адрес доставки.')
            return {"success": False, "error": "Не передан адрес доставки.", "status": status.HTTP_400_BAD_REQUEST}

        data = {
            "route_points": [
                {"fullname": "Санкт-Петербург, 11-я Красноармейская улица, 11"},
                {"fullname": f"Санкт-Петербург, {address}"}],
        }

        try:
            yandex_response = requests.post('https://b2b.taxi.yandex.net/b2b/cargo/integration/v2/check-price', headers=headers, json=data)
            yandex_response.raise_for_status()
            yandex_data = yandex_response.json()
            return {"success": True, "price": round(float(yandex_data['price'])), "distance_meters": yandex_data['distance_meters']}
        except requests.RequestException as e:
            logger.critical(f'Ошибка при попытке отправить запрос к API Яндекс:{e}')
            return {"success": False, "error": "Ошибка при попытке расчета стоимости.", "status": status.HTTP_503_SERVICE_UNAVAILABLE}
        except ValueError:
            logger.error(f"Некорректный JSON в ответе от API Яндекс. Статус: {yandex_response.status_code}")
            return {"success": False, "error": "Сервис доставки временно недоступен.", "status": status.HTTP_503_SERVICE_UNAVAILABLE}

    def check_cart(self, request):
        user = request.user
        front_data = request.data.get('cart')
        if not isinstance(user, AnonymousUser):
            try:
                user_id = CustomUser.objects.get(user_id=user.user_id).user_id
                new_user_card = False
            except CustomUser.DoesNotExist:
                return {"success": False, "error": "Пользователь не найден.", "status": status.HTTP_404_NOT_FOUND}
        else:
            user_id = request.COOKIES.get('user_id', None)
            new_user_card = user_id is None
            if new_user_card:
                user_id = str(uuid.uuid4())

        user_cart = Cart()
        if not user_cart.ping():
            return {"success": False, "error": "Ошибка подключения.", "status": status.HTTP_400_BAD_REQUEST}

        try:
            card_updated = user_cart.check_cart_data(user_id=user_id, front_data=front_data)
            if card_updated is None:
                return {"success": False, "error": "Корзина пустая.", "status": status.HTTP_204_NO_CONTENT}

            user_cart.sync_cart_data(user_id=user_id, front_cart_data={'total': card_updated['total'], 'products': card_updated['updated_cart']['products'], 'add_bonuses': card_updated['add_bonuses']})
            return {"success": True, "cart_data": card_updated, "user_id": user_id, "new_user_card": new_user_card}
        except Exception as e:
            logger.error(f'По какой-то причине не удалось обновить корзину.\nОшибка: {e}')
            return {"success": False, "error": "Ошибка обновления корзины.", "status": status.HTTP_503_SERVICE_UNAVAILABLE}

    def apply_promo(self, request, promo_code):
        user = request.user
        cart_service = Cart()
        cart_data = cart_service.get_cart_data(user_id=user.user_id)
        promo = PromoSystem.objects.filter(code=promo_code, active=True).prefetch_related('promocodeuseg_set').first()

        if not promo:
            return {"success": False, "error": "Промокод не существует.", "status": status.HTTP_404_NOT_FOUND}

        if promo.one_time and not isinstance(user, AnonymousUser):
            return {"success": False, "error": f"Зарегистрируйтесь или войдите в аккаунт, чтобы использовать промокод {promo_code}.", "status": status.HTTP_400_BAD_REQUEST}

        if promo.one_time and promo.promocodeuseg_set.filter(user_id=user.user_id).exists():
            return {"success": False, "error": "Промокод уже использован.", "status": status.HTTP_400_BAD_REQUEST}

        if promo.min_sum and promo.min_sum > cart_data['total']:
            return {"success": False, "error": f"Минимальная стоимость заказа для использования промокода {promo.min_sum} р.", "status": status.HTTP_400_BAD_REQUEST}

        promo_metadata = {"promocode_id": promo.promo_id, "one_time": promo.one_time}

        if promo.type == "delivery":
            return self.apply_delivery_discount(cart_data, promo, promo_metadata)
        elif promo.amount:
            return self.apply_fixed_discount(cart_data, promo, promo_metadata)
        else:
            return self.apply_percentage_discount(cart_data, promo, promo_metadata)

    def apply_delivery_discount(self, cart_data, promo, promo_metadata):
        try:
            if cart_data['delivery_data']['method'] != "Доставка":
                return {"success": False, "error": "Невозможно применить промокод для бесплатной доставки в заказе без доставки.", "status": status.HTTP_400_BAD_REQUEST}
        except KeyError:
            return {"success": False, "error": "Невозможно применить промокод для бесплатной доставки в заказе без доставки.", "status": status.HTTP_400_BAD_REQUEST}

        promo_metadata['type'] = "delivery"
        promo_metadata['new_total'] = cart_data['total'] - cart_data['delivery_data']['cost']
        Cart().apply_promo(cart_data['customer'], promo_metadata)
        return {"success": True, "freeDelivery": True}

    def apply_fixed_discount(self, cart_data, promo, promo_metadata):
        total_after_discount = cart_data['total'] - promo.amount
        if total_after_discount < 1:
            return {"success": False, "error": f"Нельзя применить промокод, недостаточная сумма заказа. Минимальная сумма заказа {promo.min_sum} р.", "status": status.HTTP_400_BAD_REQUEST}

        promo_metadata['type'] = "fixed"
        promo_metadata['new_total'] = total_after_discount
        promo_metadata['discount_value'] = promo.amount

        Cart().apply_promo(cart_data['customer'], promo_metadata)
        return {"success": True, "amount": promo.amount}

    def apply_percentage_discount(self, cart_data, promo, promo_metadata):
        discount_value = round(cart_data['total'] * (promo.procentage * 0.01))
        new_total = cart_data['total'] - discount_value

        promo_metadata['type'] = "percentage"
        promo_metadata['new_total'] = new_total
        promo_metadata['discount_value'] = promo.procentage
        Cart().apply_promo(cart_data['customer'], promo_metadata)
        return {"success": True, "percentage": promo.procentage}

    def process_payment(self, request):
        reg_user = request.user
        bonuses = request.data.get('usedBonus')
        user_data = request.data.get('userData')
        delivery_data = request.data.get('deliveryData')
        comment = request.data.get('comment')

        if not isinstance(reg_user, AnonymousUser):
            try:
                user_id = CustomUser.objects.get(user_id=reg_user.user_id).user_id
            except CustomUser.DoesNotExist:
                return {"success": False, "error": "Пользователь не найден.", "status": status.HTTP_404_NOT_FOUND}
        else:
            user_id = request.COOKIES.get('user_id', None)
            if not user_id:
                logger.error("По какой-то причине не удалось опознать корзину клиента.")
                return {"success": False, "error": "Что-то пошло не так, убедитесь что корзина не пустая.", "status": status.HTTP_400_BAD_REQUEST}

        payment = PaymentYookassa()
        user_cart = Cart()
        if not user_cart.ping():
            return {"success": False, "error": "Ошибка подключения Корзины.", "status": status.HTTP_400_BAD_REQUEST}

        order = Order()
        user_cart.add_delivery(user_id, delivery_data, user_data, comment)
        cart_data = user_cart.get_cart_data(user_id=user_id)

        order_number = order.get_neworder_num(user_id)

        if bonuses:
            try:
                UserBonusSystem.deduct_bonuses(user_id=user_id, bonuses=bonuses)
            except Exception as e:
                logger.error(f"Неудалось списать бонусы с баланса пользователя id {user_id}. Ошибка: {e}")
                return {"success": False, "error": "Неудалось списать бонусы в счёт заказа.", "status": status.HTTP_400_BAD_REQUEST}

        response = json.loads(payment.send_payment_request(user_data=user_data, cart=cart_data, order_id=order_number, delivery_data=delivery_data, bonuses=bonuses))

        if not response:
            return {"success": False, "error": "Во время оформления заказа произошла ошибка.", "status": status.HTTP_503_SERVICE_UNAVAILABLE}

        user_cart.add_payment_data(user_id=user_id, payment_id=response['id'], order_number=order_number, bonuses=bonuses)
        return {"success": True, "redirect_url": response['confirmation']['confirmation_url']}