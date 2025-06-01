from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from celery.result import AsyncResult

from ..models import *
from ..serializers import (
    CategorySerializer,
    LimitTimeProductSerializer,
    ProductSerializer,
    SubcategorySerializer,
)


class CategoryList(generics.ListAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class SubcategoryList(generics.ListAPIView):
    serializer_class = SubcategorySerializer

    def get_queryset(self):
        category_id = self.request.query_params.get("category")
        return Subcategory.objects.filter(category=category_id)


class ProductList(generics.ListAPIView):
    serializer_class = ProductSerializer

    def get_queryset(self):
        subcategory_id = self.request.query_params.get("subcategory")
        return Product.objects.filter(subcategory=subcategory_id)


class ProductAutocompleteView(APIView):
    def get(self, request, *args, **kwargs):
        query = request.query_params.get("term", "")
        products = Product.objects.filter(name__icontains=query)[:10]
        serializer = ProductSerializer(products, many=True)
        return Response(serializer.data)


class StopDiscountView(APIView):
    def post(self, request, discount_id, format=None):
        try:
            discount = Discount.objects.get(pk=discount_id)
            if discount.task_id_start:
                AsyncResult(id=discount.task_id_start).revoke(terminate=True)
            AsyncResult(id=discount.task_id_end).revoke(terminate=True)
            discount.end = timezone.now()
            discount.save()
            return Response({"status": "success"}, status=status.HTTP_200_OK)
        except Discount.DoesNotExist:
            return Response(
                {"status": "error", "message": "Discount not found"},
                status=status.HTTP_404_NOT_FOUND,
            )


class DeleteDayProduct(APIView):
    def delete(self, request, limittimeproduct_id, format=None):
        try:
            day_product = LimitTimeProduct.objects.get(pk=limittimeproduct_id)
            if day_product.task_id:
                AsyncResult(id=day_product.task_id).revoke(terminate=True)
            day_product.delete()
            return Response({"status": "success"}, status=status.HTTP_200_OK)
        except LimitTimeProduct.DoesNotExist:
            return Response(
                {"status": "error", "message": "Day Product not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
