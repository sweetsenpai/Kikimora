from rest_framework import serializers

from shop.models import Category

from .subcategory import MenuSubcategorySerializer


class CategorySerializer(serializers.ModelSerializer):
    subcategories = MenuSubcategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ["category_id", "name", "subcategories"]
