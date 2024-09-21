from rest_framework import serializers
from .models import Category, Subcategory, Product, Discount, LimitTimeProduct


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['category_id', 'name']


class SubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = ['subcategory_id', 'name']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['product_id', 'name']


class DiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Discount
        fields = ['discount_id', 'discount_type', 'value', 'description', 'min_sum', 'start', 'end', 'category',
                  'subcategory', 'product']


class LimitTimeProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = LimitTimeProduct
        fields = ['limittimeproduct_id', 'product_id', 'price', 'ammount', 'due', 'task_id']