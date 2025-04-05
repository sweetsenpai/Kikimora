from rest_framework import serializers

from shop.models import Product

from .base import BaseProductSerializer


class ProductSearchSerializer(BaseProductSerializer):
    mini_photos = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "permalink",
            "name",
            "final_price",
            "mini_photos",
            "weight",
            "available",
        ]

    def get_mini_photos(self, obj):
        return self.context.get("mini_photo_map", {}).get(obj.product_id, [])
