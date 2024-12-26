from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from celery.result import AsyncResult
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework import generics, status
from django.contrib.auth.models import update_last_login
from django.contrib.auth import authenticate
from django.db import transaction
from ..models import *
from ..serializers import *
from ..caches import *
import json
import requests
import re
import os
from ..MongoIntegration.Cart import Cart
from pymongo import MongoClient
from dotenv import load_dotenv
import logging
load_dotenv()
logger = logging.getLogger('shop')


class CategoryList(generics.ListAPIView):
    queryset = Category.objects.filter(visibility=True).prefetch_related('subcategories')
    serializer_class = CategorySerializer


class ProductApi(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        product_id = self.kwargs.get('product_id')
        return Product.objects.filter(product_id=product_id)


class ProductViewSet(viewsets.ViewSet):
    serializer_class = ProductSerializer

    @action(detail=False, methods=['get'], url_path='subcategory/(?P<subcategory_id>[^/.]+)')
    def by_subcategory(self, request, subcategory_id=None):
        products = get_products_sub_cash(f"products_sub_{subcategory_id}", subcategory_id)
        serializer = self.serializer_class(products, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='category/(?P<category_id>[^/.]+)')
    def by_category(self, request, category_id=None):
        subcategories = Subcategory.objects.filter(category_id=category_id)
        products = get_products_sub_cash(f"products_sub_{subcategory_id}", subcategory_id)
        serializer = self.serializer_class(products, many=True)
        return Response(serializer.data)


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
                print(f'Задача удалена! info:{day_product.task_id}')
            day_product.delete()
            return Response({'status': 'success'}, status=status.HTTP_200_OK)
        except LimitTimeProduct.DoesNotExist:
            return Response({'status': 'error', 'message': 'Day Product not found'}, status=status.HTTP_404_NOT_FOUND)


class LimitProduct(generics.ListAPIView):
#    queryset = get_promo_cash()
    serializer_class=LimitTimeProductSerializer


class Login(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        user = authenticate(request, email=email, password=password)

        if user:
            refresh = RefreshToken.for_user(user)
            update_last_login(None, user)

            return Response({
                "message": "Успешный вход.",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }, status=status.HTTP_200_OK)
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
            return Response({
                "message": "Пользователь успешно зарегистрирован.",
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
                "user": UserDataSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        else:
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDataView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        if not user.is_staff:
            user_id = user.user_id
        else:
            user_id = kwargs.get('user_id', user.user_id)

        try:
            user_data = CustomUser.objects.get(user_id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": "Пользователь не найден."}, status=404)
        serializer = UserDataSerializer(user_data)
        return Response(serializer.data)


class UpdateCRM(APIView):
    def get(self, request):
        insales_url = os.getenv("INSALES_URL")
        products = Product.objects.all()
        for product in products:
            response = requests.post(url=insales_url+'collects.json', json={
                "collect": {
                    "collection_id": product.subcategory.subcategory_id,
                    "product_id": product.product_id}
            })
            if response.status_code == 201:
                logger.info(f'{product.name} успешно добавлен в {product.subcategory.name}!')
            else:
                print(response.status_code)
                print(response.text)
        return Response(status=status.HTTP_201_CREATED)


class CheckCRMChanges(APIView):
    def get(self, request):
        insales_url = os.getenv("INSALES_URL")
        sub_page = 1

        while True:
            # Получение данных о подкатегориях (коллекциях)
            sub_response = requests.get(f"{insales_url}collections.json", params={"page": sub_page}).json()
            if not sub_response:
                break

            for subcat in sub_response:
                if "сайт" in subcat["title"]:
                    # Проверяем, существует ли подкатегория в базе
                    subcategory, created = Subcategory.objects.get_or_create(
                        subcategory_id=subcat["id"],
                        defaults={
                            "name": subcat["title"].replace("сайт", "").strip(),
                            "category": Category.objects.get(category_id=1),
                        },
                    )
                    if created:
                        logger.info(f"Добавлена новая подкатегория: {subcategory.name}")

                    # Получение товаров из коллекции
                    prod_response = requests.get(
                        f"{insales_url}collects.json", params={"collection_id": subcat["id"]}
                    ).json()

                    if prod_response:
                        product_list = []  # Список для массовой вставки товаров
                        product_photos = []  # Список для массовой вставки фотографий товаров
                        subcategories_for_products = {}  # Словарь для подкатегорий товаров

                        for product in prod_response:
                            # Получение данных о товаре
                            prod_data = requests.get(f"{insales_url}products/{product['product_id']}.json").json()

                            # Проверяем, существует ли товар в базе
                            if not Product.objects.filter(product_id=prod_data["id"]).exists():
                                # Создаем новый товар
                                new_prod = Product(
                                    product_id=prod_data["id"],
                                    name=re.sub(r"\s*\(.*?\)\s*", "", prod_data["title"]),
                                    description=prod_data["description"],
                                    price=float(prod_data["variants"][0]["price_in_site_currency"]),
                                    weight=prod_data["variants"][0]["weight"],
                                    bonus=round(float(prod_data["variants"][0]["price_in_site_currency"]) * 0.01),
                                )
                                product_list.append(new_prod)

                                # Добавляем подкатегории для товара
                                linked_subcategories = Subcategory.objects.filter(
                                    subcategory_id__in=prod_data.get("collections_ids", [])
                                )
                                if linked_subcategories.exists():
                                    subcategories_for_products[new_prod] = linked_subcategories

                                # Сохраняем фотографии товара
                                for image in prod_data["images"]:
                                    photo = ProductPhoto(
                                        product=new_prod,  # Привязываем фотографию к текущему товару
                                        photo_url=image["external_id"],
                                        is_main=(image["position"] == 1),
                                    )
                                    product_photos.append(photo)

                        # После цикла сохраняем товары и фотографии в транзакции
                        with transaction.atomic():
                            # Массовая вставка товаров
                            if product_list:
                                Product.objects.bulk_create(product_list)

                            # Привязываем подкатегории ко всем товарам
                            for product, subcategories in subcategories_for_products.items():
                                product.subcategory.add(*subcategories)

                            # Массовая вставка фотографий товаров
                            if product_photos:
                                ProductPhoto.objects.bulk_create(product_photos)

                        logger.info(f"{len(product_list)} товаров и {len(product_photos)} фотографий добавлено в базу данных.")

            sub_page += 1

        return Response(status=status.HTTP_201_CREATED)


class YandexCalculation(APIView):
    def post(self, request, *args, **kwargs):
        token = os.getenv('YANDEX_TOKEN')
        headers = {"Authorization": f"Bearer {token}",
                   'Accept-Language': 'ru/ru'}
        address = request.data.get('address')
        if not address:
            logger.error('Не передан адрес доставки.')
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
            logger.error(f'Ошибка при попытке отправить запрос к API Яндекс:{e}')
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
            logger.error('Передан не верный токен yandex-delivery.')
            return Response({"error": default_error_msg},
                            status=status.HTTP_401_UNAUTHORIZED)
        else:
            logger.error(f'Непредвиденная ошибка во время расчета стоимости заказ.\nAddres:{request}\n ERROR:{yandex_data}')
            return Response({"error": default_error_msg},
                            status=yandex_response.status_code)


class CheckCart(APIView):
    def post(self, request):
        front_data = request.data.get('cart')
        user_id = 1
        x = Cart(MongoClient(os.getenv("MONGOCON")))
        if not x.ping():
            return Response({"error": "Ошибка подключения."}, status=status.HTTP_400_BAD_REQUEST)
        print(x.check_cart_data(user_id=1, front_data=x.get_cart_data(1)))
        return Response(status=status.HTTP_200_OK)
