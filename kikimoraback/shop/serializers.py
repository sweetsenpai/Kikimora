from rest_framework import serializers
from .models import Category, Subcategory, Product, Discount, LimitTimeProduct


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['product_id', 'name', 'description', 'price', 'photo_url', 'subcategory']


class SubcategorySerializer(serializers.ModelSerializer):
    products = ProductSerializer(many=True, read_only=True)

    class Meta:
        model = Subcategory
        fields = ['subcategory_id', 'name', 'category', 'products']


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubcategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ['category_id', 'name', 'subcategories']


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ['discount_id', 'discount_type', 'value', 'description', 'min_sum', 'start', 'end', 'category',
                  'subcategory', 'product']


class LimitTimeProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = LimitTimeProduct
        fields = ['limittimeproduct_id', 'product_id', 'price', 'ammount', 'due', 'task_id']