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
    category = CategorySerializer(read_only=True)
    subcategory = SubcategorySerializer(read_only=True)
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Discount
        fields = ['discount_id', 'discount_type', 'value', 'description', 'min_sum', 'start', 'end', 'category',
                  'subcategory', 'product']


class LimitTimeProductSerializer(serializers.ModelSerializer):
    product_id = ProductSerializer(read_only=True)

    class Meta:
        model = LimitTimeProduct
        fields = ['limittimeproduct_id', 'price', 'ammount', 'due', 'task_id', 'product_id']