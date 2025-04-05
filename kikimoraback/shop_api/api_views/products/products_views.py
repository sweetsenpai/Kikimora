from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination

from shop.services.caches import (
    active_products_cache,
    get_discounted_product_data,
    subcategory_cache,
)
from shop_api.serializers import ProductCardSerializer, ProductSearchSerializer
from shop_api.tasks.db_tasks.cache_tasks.cache_prices_tasks import update_price_cache


def sort_producst(products_set, query_params: str):
    """
    Функция для сортировки товаров по цене или весу, по возрастанию или убыванию.
    Args:
        products_set: QuerySet товаров
        query_params: Фильтр, который будет применен для этой функции
    """
    # Конечно в будующем лучше реализовать кеширование результатов работы этой функции,
    # но пока этого достаточно
    if query_params == "price_asc":
        products_set = products_set.order_by("price")
    if query_params == "price_des":
        products_set = products_set.order_by("-price")
    if query_params == "weight_asc":
        products_set = products_set.order_by("weight")
    if query_params == "weight_des":
        products_set = products_set.order_by("-weight")
    return products_set


class ProductViewSet(viewsets.ViewSet):
    serializer_class = ProductCardSerializer
    pagination_class = PageNumberPagination
    page_size = 8

    @action(detail=False, methods=["get"], url_path="all-products")
    def all_products(self, request):
        cached_data = update_price_cache()
        products = active_products_cache()
        sort_by = request.query_params.get("sort_by", None)
        if sort_by:
            products = sort_producst(products, query_params=sort_by)
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(products, request)

        context = {
            "price_map": cached_data["price_map"],
            "discounts_map": cached_data["discounts_map"],
            "mini_photo_map": cached_data["mini_photo_map"],
        }

        serializer = self.serializer_class(result_page, many=True, context=context)
        return paginator.get_paginated_response(serializer.data)

    @action(
        detail=False, methods=["get"], url_path="subcategory/(?P<subcategory_id>[^/.]+)"
    )
    def by_subcategory(self, request, subcategory_slug=None):
        if not subcategory_slug.isdigit():
            subcategory = subcategory_cache().filter(permalink=subcategory_slug).first()
            subcategory_id = subcategory.subcategory_id
        else:
            subcategory_id = subcategory_slug
        cached_data = update_price_cache()
        products = active_products_cache(subcategory_id)
        sort_by = request.query_params.get("sort_by", None)
        if sort_by:
            products = sort_producst(products, sort_by)
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(products, request)
        context = {
            "price_map": cached_data["price_map"],
            "discounts_map": cached_data["discounts_map"],
            "mini_photo_map": cached_data["mini_photo_map"],
        }

        serializer = self.serializer_class(result_page, many=True, context=context)

        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"], url_path="with-discounts")
    def with_discounts(self, request):
        """
        Возвращает все товары, к которым применены скидки.
        """
        # Получаем список ID товаров со скидками из кэша

        # Получаем полные данные о товарах по их ID
        products_with_discounts = get_discounted_product_data()
        # Пагинация результатов
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(products_with_discounts, request)

        # Получаем кэшированные данные для контекста
        cached_data = update_price_cache()

        context = {
            "price_map": cached_data["price_map"],
            "discounts_map": cached_data["discounts_map"],
            "mini_photo_map": cached_data["mini_photo_map"],
        }

        # Сериализуем данные
        serializer = self.serializer_class(result_page, many=True, context=context)

        return paginator.get_paginated_response(serializer.data)

    @action(detail=False, methods=["get"], url_path="search-product")
    def search_product(self, request):
        """
        Метод для поиска по товарам
        """
        query = request.query_params.get("query", None)
        if not query:
            return Response({"detail": "Парметр 'query' обязателен."}, status=400)

        cached_data = update_price_cache()
        products = active_products_cache().filter(name__icontains=query)
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(products, request)
        context = {
            "price_map": cached_data["price_map"],
            "discounts_map": cached_data["discounts_map"],
            "mini_photo_map": cached_data["mini_photo_map"],
        }

        serializer = ProductSearchSerializer(result_page, many=True, context=context)

        return Response(serializer.data)
