from rest_framework import serializers

class OrderPathSerializer(serializers.Serializer):
    steps = serializers.ListField(
        child=serializers.ChoiceField(choices=[
            "delivery_step", "check_cart_step", "promo_code_step", "payment_step"
        ]),
        required=True
    )
    cart = serializers.DictField(required=False)
    userData = serializers.DictField(required=False)
    deliveryData = serializers.DictField(required=False)
    usedBonus = serializers.IntegerField(required=False, allow_null=True)
    comment = serializers.CharField(required=False, allow_blank=True)
