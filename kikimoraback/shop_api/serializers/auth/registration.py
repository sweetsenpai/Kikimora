from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from shop.models import CustomUser


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    class Meta:
        model = CustomUser
        fields = ("email", "user_fio", "phone", "bd", "password")

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data["email"],
            user_fio=validated_data["user_fio"],
            phone=validated_data["phone"],
            bd=validated_data["bd"],
            password=validated_data["password"],
        )
        return user
