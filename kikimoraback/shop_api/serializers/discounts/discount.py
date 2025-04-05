from rest_framework import serializers

from shop.models import Discount, Product

from ..categories.category import CategorySerializer
from ..categories.subcategory import SubcategorySerializer
from ..products.detail import ProductSerializer


class MenuDiscountProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["product_id", "name"]


class DiscountSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    subcategory = SubcategorySerializer(read_only=True)
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Discount
        fields = [
            "discount_id",
            "discount_type",
            "value",
            "description",
            "start",
            "end",
            "category",
            "subcategory",
            "product",
        ]
