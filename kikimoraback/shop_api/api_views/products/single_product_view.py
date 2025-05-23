import logging

from django.http import Http404

from rest_framework import generics, status
from rest_framework.response import Response

from shop.models import Product
from shop.services.caches import active_products_cache
from shop.tasks import update_price_cache
from shop_api.serializers import ProductSerializer

logger = logging.getLogger(__name__)


class ProductApi(generics.RetrieveAPIView):
    serializer_class = ProductSerializer

    def get_object(self):
        product_slug = self.kwargs.get("product_slug")

        # Получаем один товар по ID
        try:
            if product_slug.isdigit():
                single_product = active_products_cache().get(product_id=product_slug)
            else:
                single_product = active_products_cache().get(permalink=product_slug)
        except Product.DoesNotExist:
            logger.error(
                f"Неудалось найти товаро по заданным параметрам.{product_slug}"
            )
            raise Http404
        # Возвращаем объект продукта
        return single_product

    def get_serializer_context(self):
        # Добавляем контекст для сериализатора
        cached_data = update_price_cache()
        return {
            "price_map": cached_data["price_map"],
            "discounts_map": cached_data["discounts_map"],
            "photos_map": cached_data["photos_map"],
        }
