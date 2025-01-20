from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import AnonymousUser
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.pagination import PageNumberPagination
from celery.result import AsyncResult
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import generics, status
from django.contrib.auth.models import update_last_login
from django.contrib.auth import authenticate
from django.db import transaction
from ..models import *
from ..serializers import *
from ..caches import *
import json
import requests
import uuid
import re
import os
from ..MongoIntegration.Cart import Cart
from ..MongoIntegration.Order import Order
from ..API.yookassa_api import PaymentYookassa
from ..API.insales_api import send_new_order
from yookassa.domain.notification import WebhookNotificationEventType, WebhookNotificationFactory
from yookassa.domain.common import SecurityHelper
from dotenv import load_dotenv
import logging
import random
from yookassa import Webhook
from ..tasks import new_order_email

load_dotenv()
logger = logging.getLogger('shop')
logger.setLevel(logging.DEBUG)


class CategoryList(generics.ListAPIView):
    queryset = Category.objects.filter(visibility=True).prefetch_related('subcategories')
    serializer_class = CategorySerializer


class MenuSubcategory(generics.ListAPIView):
    queryset = subcategory_cash()
    serializer_class = MenuSubcategorySerializer


class ProductApi(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        return Product.objects.filter(product_id=product_id)


class ProductViewSet(viewsets.ViewSet):
    serializer_class = ProductSerializer
    pagination_class = PageNumberPagination

    @action(detail=False, methods=['get'], url_path='subcategory/(?P<subcategory_id>[^/.]+)')
    def by_subcategory(self, request, subcategory_id=None):
        products = get_products_sub_cash(f"products_sub_{subcategory_id}", subcategory_id)
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(products.order_by('name'), request)
        serializer = self.serializer_class(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'], url_path='category/(?P<category_id>[^/.]+)')
    def by_category(self, request, category_id=None):
        subcategories = Subcategory.objects.filter(category_id=category_id)
        products = get_products_sub_cash(f"products_sub_{subcategory_id}", subcategory_id)
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(products, request)
        serializer = self.serializer_class(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


class ProductAutocompleteView(APIView):
    def get(self, request, *args, **kwargs):
        query = request.query_params.get('term', '')
        products = Product.objects.filter(name__icontains=query)[:10]
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class DiscountProductActiveList(generics.ListAPIView):
    queryset = get_discount_cash()
    serializer_class=DiscountSerializer


class StopDiscountView(APIView):
    def post(self, request, discount_id, format=None):
        try:
            discount = Discount.objects.get(pk=discount_id)
            if discount.task_id_start:
                AsyncResult(id=discount.task_id_start).revoke(terminate=True)
            AsyncResult(id=discount.task_id_end).revoke(terminate=True)
            discount.end = timezone.now()
            discount.save()
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        except Discount.DoesNotExist:
            return Response({'status': 'error', 'message': 'Discount not found'}, status=status.HTTP_404_NOT_FOUND)


class DeleteDayProduct(APIView):
    def delete(self, request, limittimeproduct_id, format=None):
        try:
            day_product = LimitTimeProduct.objects.get(pk=limittimeproduct_id)
            if day_product.task_id:
                AsyncResult(id=day_product.task_id).revoke(terminate=True)
                logger.info(f'Задача удалена! info:{day_product.task_id}')
            day_product.delete()
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        except LimitTimeProduct.DoesNotExist:
            return Response({'status': 'error', 'message': 'Day Product not found'}, status=status.HTTP_404_NOT_FOUND)


class LimitProduct(generics.ListAPIView):
    queryset = get_promo_cash()
    serializer_class=LimitTimeProductSerializer


class Login(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, email=email, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            update_last_login(None, user)

            response = JsonResponse({
                "message": "Успешный вход.",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }, status=status.HTTP_200_OK)

            # Устанавливаем куки на сервере
            response.set_cookie("access_token", str(refresh.access_token), httponly=True, secure=True, samesite='Strict')
            response.set_cookie("refresh_token", str(refresh), httponly=True, secure=True, samesite='Strict')

            return response
        else:
            return Response(
                {"error": "Неверный логин или пароль."},
                status=status.HTTP_401_UNAUTHORIZED
            )

class RegisterUserView(APIView):
    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)

            response = JsonResponse({
                "message": "Пользователь успешно зарегистрирован.",
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                "user": UserDataSerializer(user).data
            }, status=status.HTTP_201_CREATED)

            # Устанавливаем куки на сервере
            response.set_cookie("access_token", str(refresh.access_token), httponly=True, secure=True, samesite='Strict')
            response.set_cookie("refresh_token", str(refresh), httponly=True, secure=True, samesite='Strict')

            return response
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDataView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    serializer_class = UserDataSerializer

    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_staff:
            user_id = user.user_id
        else:
            user_id = kwargs.get('user_id', user.user_id)

        try:
            user_data = CustomUser.objects.get(user_id=user_id)
            serializer = self.serializer_class(user_data, many=False)
        except CustomUser.DoesNotExist:
            return Response({"error": "Пользователь не найден."}, status=404)
        return Response(status=status.HTTP_200_OK,data=serializer.data)

    def put(self, request, **kwargs):
        user = request.user
        user_id = kwargs.get('user_id', user.user_id)
        new_password = request.data.get('new_password')
        old_password = request.data.get('old_password')
        if not user.is_staff and user.user_id != user_id:
            return Response({"error": "У вас нет прав для изменения этих данных."}, status=403)

        try:
            user_data = CustomUser.objects.get(user_id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": "Пользователь не найден."}, status=404)

        if old_password and not user.check_password(old_password):
            return Response({"error": "Неверный старый пароль."}, status=400)

        if new_password:
            user.set_password(new_password)

        serializer = self.serializer_class(user_data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            if new_password:
                user.save()
            return Response(status=status.HTTP_200_OK, data=serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class YandexCalculation(APIView):

    def post(self, request, *args, **kwargs):
        token = os.getenv('YANDEX_TOKEN')
        headers = {"Authorization": f"Bearer {token}",
                   'Accept-Language': 'ru/ru'}
        address = request.data.get('address')
        if not address:
            logger.warning('Не передан адрес доставки.')
            return Response({"error": "Не передан адрес доставки."},
                            status=status.HTTP_400_BAD_REQUEST)
        data = {
            "route_points": [
                {"fullname": "Санкт-Петербург, 11-я Красноармейская улица, 11"},
                {"fullname": f"Санкт-Петербург, {address}"}],
        }
        try:
            yandex_response = requests.post('https://b2b.taxi.yandex.net/b2b/cargo/integration/v2/check-price',
                                            headers=headers, json=data)
        except requests.RequestException as e:
            logger.critical(f'Ошибка при попытке отправить запрос к API Яндекс:{e}')
            return Response({"error": "Ошибка при попытке расчета стоимости.\n"
                                      "Попробуйте оформить заказ позже или обратитесь в магазин."},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            yandex_data = yandex_response.json()
        except ValueError:
            logger.error(f"Некорректный JSON в ответе от API Яндекс. Статус: {yandex_response.status_code}")
            return Response({"error": "Сервис доставки временно недоступен."},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)

        default_error_msg = "Сейчас серфис доставки не доступен.\nВы можете оформить доставку самостоятельно или обратиться в магазин."

        if yandex_response.ok:
            return Response(status=status.HTTP_200_OK, data={'price': round(float(yandex_data['price'])),
                                                             'distance_meters': yandex_data['distance_meters']})
        elif yandex_response.status_code == 400:
            logger.error(f'Ошибка во время расчета стоимости заказ.\nAddres:{address}\n ERROR:{yandex_data}')
            return Response({"error": "Не удалось расчитать стоимость доставки.\n"
                                      "Проверьте правильность введенного адреса или повторите попытку позже."},
                            status=status.HTTP_400_BAD_REQUEST)
        elif yandex_response.status_code == 401:
            logger.critical('Передан не верный токен yandex-delivery.')
            return Response({"error": default_error_msg},
                            status=status.HTTP_401_UNAUTHORIZED)
        else:
            logger.error(f'Непредвиденная ошибка во время расчета стоимости заказ.\nAddres:{request}\n ERROR:{yandex_data}')
            return Response({"error": default_error_msg},
                            status=yandex_response.status_code)


class CheckCart(APIView):
    def post(self, request):
        front_data = request.data.get('cart')
        promo = request.data.get('cart')
        user = request.user
        if not isinstance(user, AnonymousUser):
            try:
                user_id = CustomUser.objects.get(user_id=user.user_id).user_id
                new_user_card = False
            except CustomUser.DoesNotExist:
                return Response({"error": "Пользователь не найден."}, status=status.HTTP_404_NOT_FOUND)
        else:
            user_id = request.COOKIES.get('user_id', None)
            new_user_card = user_id is None  # Если куки нет, значит, это новый пользователь
            if new_user_card:
                user_id = str(uuid.uuid4())

        # Подключаемся к базе данных
        user_cart = Cart()
        if not user_cart.ping():
            return Response({"error": "Ошибка подключения."}, status=status.HTTP_400_BAD_REQUEST)

        # Обрабатываем данные корзины
        try:
            card_updated = user_cart.check_cart_data(user_id=user_id, front_data=front_data)
        except Exception as e:
            logger.error(f'По какой-то причине не удалось обновить корзину.\nОшибка: {e}')
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if card_updated is None:
            # Если корзина пустая, возвращаем ответ с куки
            response = Response({"Корзина пустая"}, status=status.HTTP_204_NO_CONTENT)
            if new_user_card:
                response.set_cookie('user_id', user_id, max_age=60*60*24*30, httponly=True)
            return response

        # Синхронизируем корзину
        user_cart.sync_cart_data(user_id=user_id, front_cart_data={'total': card_updated['total'],
                                                                   'products': card_updated['updated_cart']['products']})

        response = Response(status=status.HTTP_200_OK, data=card_updated)
        # if promo:
        #     user_cart.apply_promo(promo)
        if isinstance(user, AnonymousUser):
            user_cart.add_unregistered_mark(user_id=user_id)
            response.set_cookie('user_id', user_id, max_age=60*60*24*30, httponly=True)
        return response


class SyncCart(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        front_data = request.data.get('cart')
        user = request.user
        try:
            user_data = CustomUser.objects.get(user_id=user.user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": "Пользователь не найден."}, status=404)
        cart = Cart(os.getenv('MONGOCON'))
        return Response(data=cart.sync_cart_data(user_id=user_data.user_id, front_cart_data=front_data['cart'])['products'], status=status)


class CheckPromo(APIView):
    def post(self, request):
        promo = request.data.get('promo_code')
        all_pormos = get_promo_cash()
        promo_data = all_pormos.odjects.filter(code=promo)

        if not promo_data:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if promo_data.type =='delivery':
            return Response(status=status.HTTP_200_OK, data={'free_delivery': True})
        if promo_data.one_time:
            if check_promo_one_time(user_id, promo):
                return Response(status=status.HTTP_409_CONFLICT)
        user_cart = []
        return Response(status=status.HTTP_200_OK)


class Payment(APIView):
    def post(self, request):
        reg_user = request.user
        user_data = request.data.get('userData')
        delivery_data = request.data.get('deliveryData')
        comment = request.data.get('comment')
        if not isinstance(reg_user, AnonymousUser):
            try:
                user_id = CustomUser.objects.get(user_id=reg_user.user_id).user_id
            except CustomUser.DoesNotExist:
                return Response({"error": "Пользователь не найден."}, status=status.HTTP_404_NOT_FOUND)
        else:
            user_id = request.COOKIES.get('user_id', None)
            if not user_id:
                logger.error("По какой-то причине не удалось опознать корзину клиента.")
                return Response({"error": "Что-то пошло не так, убедитесь что корзина не пустая.\n"
                                          "Обновите страницу и попробуйте оформить заказ ещё раз, "
                                          "если ошибка не исчезла, "
                                          "то свяжитесь с магазином и поможем с оформление заказа."})

        payment = PaymentYookassa()
        user_cart = Cart()
        if not user_cart.ping():
            return Response({"error": "Ошибка подключения Корзины."}, status=status.HTTP_400_BAD_REQUEST)
        order = Order()
        user_cart.add_delivery(user_id, delivery_data, user_data, comment)
        cart_data = user_cart.get_cart_data(user_id=user_id)
        order_number = order.get_neworder_num(user_id)
        response = json.loads(payment.send_payment_request(user_data=user_data,
                                                           cart=cart_data,
                                                           order_id=order_number,
                                                           delivery_data=delivery_data))
        if not response:
            return Response({"error": "Во время оформления заказа произошла ошибка.\n"
                                      "Попробуйте перезагрузить страниц."},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)
        user_cart.add_payement_data(user_id=user_id, payment_id=response['id'], order_number=order_number)

        return Response(status=200, data={'paymentLink': response['confirmation']['confirmation_url']})


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


@csrf_exempt
def yookassa_webhook(request):
    ip = get_client_ip(request)
    if not SecurityHelper().is_ip_trusted(ip):
        logger.warning("Поптыка получить доступ к api оплаты из незарегистрированного источника.")
        return HttpResponse(status=400)

    event_json = json.loads(request.body)
    try:
        notification_object = WebhookNotificationFactory().create(event_json)
        response_object = notification_object.object

        if notification_object.event == WebhookNotificationEventType.PAYMENT_SUCCEEDED:
            payment_id = response_object.id
            user_cart = Cart()
            user_order = Order()
            if not user_cart.ping():
                return Response(status=status.HTTP_400_BAD_REQUEST)
            user_cart_data = user_cart.get_cart_data(payment_id=payment_id)
            user_order.create_order_on_cart(user_cart_data)
            if send_new_order(user_cart_data):
                new_order_email(user_cart_data)
                user_cart.delete_cart(payment_id=payment_id)
                return Response(status=status.HTTP_200_OK)
            else:
                logging.error('Не удалось загрузить новый заказ в crm!')
                return Response(status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Ошибка при обработке вебхука Yookassa: {str(e)}, данные: {event_json}")
        return Response(status=status.HTTP_400_BAD_REQUEST)


class TestWebhook(APIView):
# TODO: поправить отображение адреса, сейчас в письме вместо квартиры NOne
# TODO: решить что-то с номерами заказов которые формирует crm
    def post(self, request):
        payment_id = "2f1b3e6c-000f-5000-b000-13d319182a5e"
        user_cart = Cart()
        user_order = Order()
        if not user_cart.ping():
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user_cart_data = user_cart.get_cart_data(payment_id=payment_id)
        if send_new_order(user_cart_data):
            user_order.create_order_on_cart(user_cart_data)
            new_order_email(user_cart_data)
            user_cart.delete_cart(payment_id=payment_id)
            return Response(status=status.HTTP_200_OK)
        else:
            logging.error('Не удалось загрузить новый заказ в crm!')
            return Response(status=status.HTTP_400_BAD_REQUEST)