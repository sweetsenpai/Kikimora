from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from celery.result import AsyncResult

from shop.models import Discount, Subcategory
from shop.services.caches import get_discount_cash
from shop_api.serializers import DiscountSerializer, MenuDiscountProductSerializer


class DiscountProductActiveList(generics.ListAPIView):
    queryset = get_discount_cash()
    serializer_class = DiscountSerializer


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


class DiscountCreationRelatedProducts(APIView):
    def get(self, request, subcategory_id=None):
        if not subcategory_id:
            return Response(
                {"error": "Необходимо передать id подкатегории"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            subcategory = (
                Subcategory.objects.filter(subcategory_id=subcategory_id)
                .prefetch_related("products")
                .first()
            )
            products = subcategory.products.all()
            serializer = MenuDiscountProductSerializer(products, many=True)
            return Response(serializer.data)
        except AttributeError:
            return Response(
                {"error": f"Категории с id {subcategory_id} не существует."},
                status=status.HTTP_404_NOT_FOUND,
            )
