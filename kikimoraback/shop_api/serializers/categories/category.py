from rest_framework import serializers
from shop.models import Category
from .subcategory import SubcategorySerializer


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubcategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['category_id', 'name', 'subcategories']
