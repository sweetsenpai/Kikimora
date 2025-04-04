from rest_framework import serializers
from shop.models import Subcategory, Product


class MenuSubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = [
            'subcategory_id',
            'name',
            'text',
            'permalink']


class SubcategorySerializer(serializers.ModelSerializer):
    products = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Product.objects.all()
    )

    class Meta:
        model = Subcategory
        fields = [
            'subcategory_id',
            'name',
            'category',
            'products'
        ]
