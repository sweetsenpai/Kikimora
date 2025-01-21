from rest_framework import serializers
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.password_validation import validate_password
from .models import *


class UserAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddress
        fields = ('address_id', 'street', 'building', 'apartment')


class UserBonusSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBonusSystem
        fields = ('bonus_id', 'bonus_ammount')


class UserDataSerializer(serializers.ModelSerializer):
    bonus = serializers.SerializerMethodField()
    address = UserAddressSerializer(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = ('email', 'user_fio', 'phone', 'bd', 'bonus', 'address')

    def get_bonus(self, obj):
        user_bonus = UserBonusSystem.objects.filter(user_bonus=obj).first()
        return user_bonus.bonus_ammount if user_bonus else 0


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = CustomUser
        fields = ('email', 'user_fio', 'phone', 'bd', 'password')

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise ValidationError("Пользователь с таким email уже существует.")
        return value

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            user_fio=validated_data['user_fio'],
            phone=validated_data['phone'],
            bd=validated_data['bd'],
            password=validated_data['password'],
        )
        return user


class ProductPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductPhoto
        fields = ['photo_id', 'product', 'photo_url', 'is_main', 'photo_description']


class ProductSerializer(serializers.ModelSerializer):
    photos = ProductPhotoSerializer(many=True, read_only=True)
    # subcategory = serializers.PrimaryKeyRelatedField(
    #     many=True, queryset=Subcategory.objects.all()
    # )

    class Meta:
        model = Product
        fields = [
            'product_id',
            'name',
            'description',
            'price',
            'photos',
            'bonus',
            'weight',
            # 'subcategory',
            'visibility'
        ]


class MenuSubcategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Subcategory
        fields = [
            'subcategory_id',
            'name']


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
            'products'  # Обновлено для Many-to-Many
        ]


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
        fields = ['discount_id', 'discount_type', 'value', 'description', 'start', 'end', 'category',
                  'subcategory', 'product']


class LimitTimeProductSerializer(serializers.ModelSerializer):
    product_id = ProductSerializer(read_only=True)

    class Meta:
        model = LimitTimeProduct
        fields = ['limittimeproduct_id', 'price', 'ammount', 'due', 'task_id', 'product_id']


