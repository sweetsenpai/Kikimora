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
from ..models import *
from ..serializers import *
from ..caches import *
import json
import requests
import re
import os
from dotenv import load_dotenv
load_dotenv()


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
                print(f'{product.name} успешно добавлен в {product.subcategory.name}!')
            else:
                print(response.status_code)
                print(response.text)
        return Response(status=status.HTTP_201_CREATED)


class ChekCRMChanges(APIView):
    def get(self, request):
        insales_url = os.getenv("INSALES_URL")
        sub_page=1
        while True:
            sub_response = requests.get(insales_url+'collections.json', params={'page': sub_page}).json()
            if not sub_response:
                break
            for subcat in sub_response:
                if "сайт" in subcat['title']:
                    if not Subcategory.objects.filter(subcategory_id=subcat['id']):
                        new_sub = Subcategory(subcategory_id=subcat['id'], name=subcat['title'].replace('сайт', ''),
                                              category=Category.objects.get(category_id=1))
                        new_sub.save()

                    prod_responce = requests.get(insales_url+f"collects.json?collection_id={subcat['id']}").json()
                    if prod_responce:
                        for product in prod_responce:
                            prod_data = requests.get(insales_url+f"products/{product['product_id']}.json").json()
                            if not Product.objects.filter(product_id=prod_data['id']):
                                new_prod = Product(product_id=prod_data['id'], name=re.sub(r'\s*\(.*?\)\s*', '',prod_data['title']),
                                                   description=prod_data['description'],
                                                   price=float(prod_data['variants'][0][
                                                                   'price_in_site_currency']),
                                                   weight=prod_data['variants'][0]['weight'],
                                                   subcategory=Subcategory.objects.get(subcategory_id=subcat['id']),
                                                   bonus=round(float(prod_data['variants'][0][
                                                                         'price_in_site_currency']) * 0.01))
                                new_prod.save()
                                for image in prod_data['images']:
                                    new_image = ProductPhoto(
                                        product=Product.objects.get(product_id=new_prod.product_id),
                                        photo_url=image['external_id'],
                                        is_main=(image['position'] == 1))
                                    new_image.save()
                                print('Успешно добавлено в БД:', new_prod.name)
            sub_page += 1
        return Response(status=status.HTTP_201_CREATED)