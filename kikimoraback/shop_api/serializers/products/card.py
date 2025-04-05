from rest_framework import serializers

from shop.models import Product

from .base import BaseProductSerializer


class ProductCardSerializer(BaseProductSerializer):
    mini_photos = serializers.SerializerMethodField()
    tag = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            "product_id",
            "name",
            "price",
            "bonus",
            "weight",
            "final_price",
            "discounts",
            "mini_photos",
            "tag",
            "permalink",
            "available",
        ]

    def get_mini_photos(self, obj):
        return self.context.get("mini_photo_map", {}).get(obj.product_id, [])

    def get_tag(self, obj):
        return obj.tag.text if obj.tag else None
