from rest_framework import serializers

from shop.models import CustomUser, UserBonusSystem


class UserBonusSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserBonusSystem
        fields = ("bonus_id", "bonus_ammount")


class UserDataSerializer(serializers.ModelSerializer):
    bonus = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            "email",
            "user_fio",
            "phone",
            "bd",
            "bonus",
            "address",
            "is_email_verified",
        )

    def get_bonus(self, obj):
        user_bonus = UserBonusSystem.objects.filter(user_bonus=obj).first()
        return user_bonus.bonus_ammount if user_bonus else 0
