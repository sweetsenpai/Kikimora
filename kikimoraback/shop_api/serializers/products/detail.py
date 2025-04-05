from rest_framework import serializers

from shop.models import Product

from .base import BaseProductSerializer


class ProductSerializer(BaseProductSerializer):
    photos = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "product_id",
            "name",
            "description",
            "price",
            "bonus",
            "weight",
            "final_price",
            "discounts",
            "photos",
            "available",
        ]

    def get_photos(self, obj):
        return self.context.get("photos_map", {}).get(obj.product_id, [])
