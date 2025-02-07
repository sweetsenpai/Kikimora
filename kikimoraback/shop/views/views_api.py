from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import AnonymousUser, update_last_login
from django.db.models import F
from django.contrib.auth import authenticate
from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from celery.result import AsyncResult
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework import generics, status
from ..serializers import *
from ..services.caches import *
import json
import requests
import uuid
import os
from ..MongoIntegration.Cart import Cart
from ..MongoIntegration.Order import Order
from ..API.yookassa_api import PaymentYookassa
from ..API.insales_api import send_new_order
from yookassa.domain.notification import WebhookNotificationEventType, WebhookNotificationFactory
from yookassa.domain.common import SecurityHelper
from dotenv import load_dotenv
import logging
from ..tasks import new_order_email, update_price_cache, process_payment_canceled, \
    process_payment_succeeded, send_confirmation_email
from ..services.email_verification import verify_email_token
from bson import json_util
from pprint import pprint
load_dotenv()
logger = logging.getLogger('shop')
logger.setLevel(logging.DEBUG)


class CategoryList(generics.ListAPIView):
    queryset = Category.objects.filter(visibility=True).prefetch_related('subcategories')
    serializer_class = CategorySerializer


class MenuSubcategory(generics.ListAPIView):
    queryset = subcategory_cash()
    serializer_class = MenuSubcategorySerializer


class ProductApi(generics.RetrieveAPIView):
    serializer_class = ProductSerializer

    def get_object(self):
        product_id = self.kwargs.get('product_id')

        # Получаем один товар по ID
        try:
            cache_key = f'single_product_{product_id}'
            single_product_cache = cache.get(cache_key)
            if not single_product_cache:
                single_product_cache = active_products_cash().get(product_id=product_id)
                cache.set(cache_key, single_product_cache, timeout=60*15)
        except Product.DoesNotExist:
            raise NotFound(detail="Product not found")

        # Возвращаем объект продукта
        return single_product_cache

    def get_serializer_context(self):
        # Добавляем контекст для сериализатора
        cached_data = update_price_cache()
        return {
            'price_map': cached_data['price_map'],
            'discounts_map': cached_data['discounts_map'],
            'photos_map': cached_data['photos_map']
        }


def sort_producst(products_set, query_params: str):
    """
    Функция для сортировки товаров по цене или весу, по возрастанию или убыванию.
    Args:
        products_set: QuerySet товаров
        query_params: Фильтр, который будет применен для этой функции
    """
    # Конечно в будующем лучше реализовать кеширование результатов работы этой функции,
    # но пока этого достаточно
    if query_params == 'price_asc':
        products_set = products_set.order_by('price')
    if query_params == 'price_des':
        products_set = products_set.order_by('-price')
    if query_params == 'weight_asc':
        products_set = products_set.order_by('weight')
    if query_params == 'weight_des':
        products_set = products_set.order_by('-weight')
    return products_set


class ProductViewSet(viewsets.ViewSet):
    serializer_class = ProductCardSerializer
    pagination_class = PageNumberPagination
    page_size = 8

    @action(detail=False, methods=['get'], url_path='all-products')
    def all_products(self, request):
        cached_data = update_price_cache()
        products = active_products_cash()
        sort_by = request.query_params.get('sort_by', None)
        if sort_by:
            products = sort_producst(products, query_params=sort_by)
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(products, request)
        context = {
            'price_map': cached_data['price_map'],
            'discounts_map': cached_data['discounts_map'],
            'photos_map': cached_data['photos_map']
        }
        serializer = self.serializer_class(
            result_page,
            many=True,
            context=context
        )
        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'], url_path='subcategory/(?P<subcategory_id>[^/.]+)')
    def by_subcategory(self, request, subcategory_id=None):
        cached_data = update_price_cache()
        products = active_products_cash(subcategory_id)
        sort_by = request.query_params.get('sort_by', None)
        if sort_by:
            products = sort_producst(products, sort_by)
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(products, request)
        context = {
            'price_map': cached_data['price_map'],
            'discounts_map': cached_data['discounts_map'],
            'photos_map': cached_data['photos_map']
        }

        serializer = self.serializer_class(
            result_page,
            many=True,
            context=context
        )

        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=['get'], url_path='with-discounts')
    def with_discounts(self, request):
        """
        Возвращает все товары, к которым применены скидки.
        """
        # Получаем список ID товаров с скидками из кэша


        # Получаем полные данные о товарах по их ID
        products_with_discounts = get_discounted_product_data()

        # Пагинация результатов
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(products_with_discounts, request)

        # Получаем кэшированные данные для контекста
        cached_data = update_price_cache()

        context = {
            'price_map': cached_data['price_map'],
            'discounts_map': cached_data['discounts_map'],
            'photos_map': cached_data['photos_map']
        }

        # Сериализуем данные
        serializer = self.serializer_class(
            result_page,
            many=True,
            context=context
        )

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
    queryset = get_limit_product_cash()
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

            response.set_cookie("access_token", str(refresh.access_token), httponly=True, secure=True, samesite='Strict')
            response.set_cookie("refresh_token", str(refresh), httponly=True, secure=True, samesite='Strict')

            send_confirmation_email(user)

            return response
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    def get(self, request, token):
        user_id = verify_email_token(token)
        if user_id:
            try:
                user = CustomUser.objects.get(user_id=user_id)
                if not user.is_email_verified:
                    user.is_email_verified = True
                    user.save()
                    return render(request, 'emails/email_confirmed.html',
                                  {'website_url': os.getenv("WEBSITE_URL")})
                else:
                    return render(request, 'emails/email_confirmed.html', {
                        'website_url': os.getenv("WEBSITE_URL"),
                        'message': 'Email уже был подтвержден ранее.'
                    })
            except CustomUser.DoesNotExist:
                pass
            return render(request, 'emails/docker-compose down email_confirmed.html', {
                'website_url': os.getenv("WEBSITE_URL"),
                'message': 'Недействительная ссылка для подтверждения.'
            })


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

    def patch(self, request, **kwargs):
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

        if new_password:
            if not user.is_staff and not old_password:
                return Response({"error": "Требуется старый пароль."}, status=400)
            if not user.is_staff and not user.check_password(old_password):
                return Response({"error": "Неверный старый пароль."}, status=400)
            user.set_password(new_password)

        serializer = self.serializer_class(user_data, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            if new_password:
                user.save()
            return Response(status=status.HTTP_200_OK, data=serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# TODO: обработка кастомного времени


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
            return Response(status=status.HTTP_200_OK, data={'price': round(float(yandex_data['price'])+200),
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
        user = request.user
        if not isinstance(user, AnonymousUser):
            try:
                user_id = CustomUser.objects.get(user_id=user.user_id).user_id
                new_user_card = False
            except CustomUser.DoesNotExist:
                return Response({"error": "Пользователь не найден."}, status=status.HTTP_404_NOT_FOUND)
        else:
            user_id = request.COOKIES.get('user_id', None)
            new_user_card = user_id is None
            if new_user_card:
                user_id = str(uuid.uuid4())

        user_cart = Cart()
        if not user_cart.ping():
            return Response({"error": "Ошибка подключения."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            card_updated = user_cart.check_cart_data(user_id=user_id, front_data=front_data)

        except Exception as e:
            logger.error(f'По какой-то причине не удалось обновить корзину.\nОшибка: {e}')
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if card_updated is None:
            response = Response({"Корзина пустая"}, status=status.HTTP_204_NO_CONTENT)
            return response
        user_cart.sync_cart_data(user_id=user_id, front_cart_data={'total': card_updated['total'],
                                                                   'products': card_updated['updated_cart']['products'],
                                                                   'add_bonuses': card_updated['add_bonuses']})

        response = Response(status=status.HTTP_200_OK, data=card_updated)
        if new_user_card:
            response.set_cookie('user_id', user_id, max_age=60 * 60 * 24 * 30, httponly=True)
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
        cart = Cart()

        return Response(data=cart.sync_cart_data(user_id=user_data.user_id, front_cart_data=front_data), status=status.HTTP_200_OK)


class PromoCode(APIView):
    def post(self, request):
        user = request.user
        cart_service = Cart()
        cart_data = cart_service.get_cart_data(user_id=user.user_id)
        promo_code = request.data.get('promoCode')
        promo = PromoSystem.objects.filter(code=promo_code, active=True).prefetch_related('promocodeuseg_set').first()
        try:
            response = self.apply_promo(cart_data, promo, user, promo_code)
        except Exception as error:
            logger.error(
                f"Ошибка применения промокода.\nPROMO: {promo}\nCART: {cart_data}\nERROR: {error}"
            )
            return Response(
                {"error": "Сейчас невозможно использовать этот промокод. Попробуйте позже."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        return response

    def apply_promo(self, cart_data, promo, user, promo_code):
        if not promo:
            return Response({"error": "Промокод не существует."}, status=status.HTTP_404_NOT_FOUND)

        if promo.one_time and not isinstance(user, AnonymousUser):
            return Response(
                {"error": f"Зарегистрируйтесь или войдите в аккаунт, чтобы использовать промокод {promo_code}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if promo.one_time and promo.promocodeuseg_set.filter(user_id=user.user_id).exists():
            return Response({"error": "Промокод уже использован."}, status=status.HTTP_400_BAD_REQUEST)

        if promo.min_sum and promo.min_sum > cart_data['total']:
            return Response(
                {"error": f"Минимальная стоимость заказа для использования промокода {promo.min_sum} р."},
                status=status.HTTP_400_BAD_REQUEST
            )

        promo_metadata = {"promocode_id": promo.promo_id, "one_time": promo.one_time}

        if promo.type == "delivery":
            return self.apply_delivery_discount(cart_data, promo, promo_metadata)

        if promo.amount:
            return self.apply_fixed_discount(cart_data, promo, promo_metadata)

        return self.apply_percentage_discount(cart_data, promo, promo_metadata)

    def apply_delivery_discount(self, cart_data, promo, promo_metadata):
        try:
            if cart_data['delivery_data']['method'] != "Доставка":
                return Response(
                    {"error": "Невозможно применить промокод для бесплатной доставки в заказе без доставки."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except KeyError:
            return Response(
                {"error": "Невозможно применить промокод для бесплатной доставки в заказе без доставки."},
                status=status.HTTP_400_BAD_REQUEST
            )

        promo_metadata['type'] = "delivery"
        promo_metadata['new_total'] = cart_data['total'] - cart_data['delivery_data']['cost']
        Cart().apply_promo(cart_data['customer'], promo_metadata)
        return Response(status=status.HTTP_200_OK, data={"freeDelivery": True})

    def apply_fixed_discount(self, cart_data, promo, promo_metadata):
        total_after_discount = cart_data['total'] - promo.amount
        if total_after_discount < 1:
            return Response(
                {
                    "error": f"Нельзя применить промокод, недостаточная сумма заказа. Минимальная сумма заказа {promo.min_sum} р."},
                status=status.HTTP_400_BAD_REQUEST
            )

        promo_metadata['type'] = "fixed"
        promo_metadata['new_total'] = total_after_discount
        promo_metadata['discount_value'] = promo.amount

        Cart().apply_promo(cart_data['customer'], promo_metadata)
        return Response(data={"amount": promo.amount}, status=status.HTTP_200_OK)

    def apply_percentage_discount(self, cart_data, promo, promo_metadata):
        discount_value = round(cart_data['total'] * (promo.procentage * 0.01))
        new_total = cart_data['total'] - discount_value

        promo_metadata['type'] = "percentage"
        promo_metadata['new_total'] = new_total
        promo_metadata['discount_value'] = promo.procentage
        Cart().apply_promo(cart_data['customer'], promo_metadata)
        return Response(data={"percentage": promo.procentage}, status=status.HTTP_200_OK)


class Payment(APIView):
    def post(self, request):
        reg_user = request.user
        bonuses = request.data.get('usedBonus')
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

        if bonuses:
            try:
                UserBonusSystem.deduct_bonuses(user_id=user_id, bonuses=bonuses)
            except Exception as e:
                logger.error(f"Неудалось списать бонусы с баланса пользователя id {user_id}. Ошибка: {e}")
                return Response({"error": "Неудалось списать бонусы в счёт заказа."}, status=status.HTTP_400_BAD_REQUEST)

        response = json.loads(payment.send_payment_request(user_data=user_data,
                                                           cart=cart_data,
                                                           order_id=order_number,
                                                           delivery_data=delivery_data,
                                                           bonuses=bonuses))

        if not response:
            return Response({"error": "Во время оформления заказа произошла ошибка.\n"
                                      "Попробуйте перезагрузить страниц."},
                            status=status.HTTP_503_SERVICE_UNAVAILABLE)
        user_cart.add_payment_data(user_id=user_id, payment_id=response['id'], order_number=order_number, bonuses=bonuses)
        order.create_order_on_cart(user_cart.get_cart_data(user_id=user_id))
        user_cart.delete_cart(user_id=user_id)
        return Response(
            {"detail": "Redirecting to payment", "redirect_url": response['confirmation']['confirmation_url']},
            status=status.HTTP_302_FOUND
        )


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
        logger.warning("Попытка получить доступ к API оплаты из незарегистрированного источника.")
        return HttpResponse(status=400)

    event_json = json.loads(request.body)
    try:
        notification_object = WebhookNotificationFactory().create(event_json)
        response_object = notification_object.object

        if notification_object.event == WebhookNotificationEventType.PAYMENT_SUCCEEDED:
            payment_id = response_object.id
            process_payment_succeeded.delay(payment_id)
        elif notification_object.event == WebhookNotificationEventType.PAYMENT_CANCELED:
            payment_id = response_object.id
            process_payment_canceled.delay(payment_id)

        return Response(status=status.HTTP_200_OK)  # Быстрый ответ YooKassa

    except Exception as e:
        logger.error(f"Ошибка при обработке вебхука YooKassa: {str(e)}, данные: {event_json}")
        return Response(status=status.HTTP_400_BAD_REQUEST)


class TestWebhook(APIView):
    def post(self, request):
        payment_id = "2f31a656-000f-5000-a000-13342c36154e"
        try:
            process_payment_succeeded(payment_id)
            return Response(status=status.HTTP_200_OK)
        except Exception as e:
            logger.debug(f"Ошибка при обработке вебхука YooKassa: {str(e)}")
            return Response(status=status.HTTP_400_BAD_REQUEST)


class UsersOrder(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]

    def post(self, request):
        try:
            user = request.user
            if not user:
                return Response({"error: Пользователь ненайден"}, status=status.HTTP_404_NOT_FOUND)
            orders = Order().get_users_orders(user.user_id)
            return Response(status=status.HTTP_200_OK, data={'orders': orders})
        except Exception as e:
            logger.error(f"Вовремя выдачи истории заказов пользователя произошла непредвиденная ошибка.\nERROR:{e}")
            return Response(status=status.HTTP_503_SERVICE_UNAVAILABLE)