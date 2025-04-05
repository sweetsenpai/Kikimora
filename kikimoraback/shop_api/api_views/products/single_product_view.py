from rest_framework import generics

from shop.services.caches import active_products_cache
from shop_api.serializers import ProductSerializer


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
            return Response(status=status.HTTP_404_NOT_FOUND)
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
