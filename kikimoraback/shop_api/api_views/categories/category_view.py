from rest_framework import generics

from shop.models import Category
from shop_api.serializers import CategorySerializer


class CategoryList(generics.ListAPIView):
    queryset = Category.objects.filter(visibility=True).prefetch_related(
        "subcategories"
    )
    serializer_class = CategorySerializer
