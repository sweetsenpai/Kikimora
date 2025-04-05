from rest_framework import serializers

from shop.models import Product


class BaseProductSerializer(serializers.ModelSerializer):
    """Базовый сериализатор товара с обработкой цен и скидок.
    Требует передачи в context:
    - price_map: dict[product_id: float]
    - discounts_map: dict[product_id: list]
    """

    final_price = serializers.SerializerMethodField()
    discounts = serializers.SerializerMethodField()

    class Meta:
        model = Product
        abstract = True
        fields = []

    def get_final_price(self, obj):
        return self.context.get("price_map", {}).get(obj.product_id, obj.price)

    def get_discounts(self, obj):
        return self.context.get("discounts_map", {}).get(obj.product_id, [])
