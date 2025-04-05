from rest_framework import generics

from shop.services.caches import subcategory_cache
from shop_api.serializers import MenuSubcategorySerializer


class MenuSubcategory(generics.ListAPIView):
    queryset = subcategory_cache()
    serializer_class = MenuSubcategorySerializer
