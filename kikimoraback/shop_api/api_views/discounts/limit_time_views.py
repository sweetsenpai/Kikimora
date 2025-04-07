from rest_framework import generics
from rest_framework.response import Response

from celery.result import AsyncResult

from shop.models import LimitTimeProduct
from shop.services.caches import get_limit_product_cash


class LimitProduct(generics.ListAPIView):
    queryset = get_limit_product_cash()
    serializer_class = LimitTimeProductSerializer


class DeleteDayProduct(APIView):
    def delete(self, request, limittimeproduct_id, format=None):
        try:
            day_product = LimitTimeProduct.objects.get(pk=limittimeproduct_id)
            if day_product.task_id:
                AsyncResult(id=day_product.task_id).revoke(terminate=True)
                logger.info(f"Задача удалена! info:{day_product.task_id}")
            day_product.delete()
            return Response({"status": "success"}, status=status.HTTP_200_OK)
        except LimitTimeProduct.DoesNotExist:
            return Response(
                {"status": "error", "message": "Day Product not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
