import pytest
from rest_framework.response import Response
from rest_framework import status

from shop_api.services.order_path_services.check_cart_service import CheckCartService


class MockCartService:
    def check_cart_data(self, front_data, user_id):
        return self.mock_response

    def sync_cart_data(self, user_id, front_cart_data):
        self.synced_data = front_cart_data


@pytest.mark.django_db
class TestCheckCartService:

    def test_empty_cart(self):
        mock_cart = MockCartService()
        service = CheckCartService(cart_service=mock_cart)

        response = service.check(user_id="test-user", cart_data={})
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"] == "В корзине ничего нет"

    def test_valid_cart(self):
        mock_cart = MockCartService()
        mock_cart.mock_response = {
            "total": 8610,
            "deleted_products": [],
            "price_mismatches": [],
            "updated_cart": {
                "products": [
                    {"product_id": 1, "name": "Test Product", "price": 1000, "bonus": 100, "quantity": 1}
                ]
            },
            "add_bonuses": 100
        }

        service = CheckCartService(cart_service=mock_cart)

        cart_data = {
            "total": 8610,
            "products": [
                {"product_id": 1, "name": "Test Product", "price": 1000, "image": [], "quantity": 1}
            ]
        }

        response = service.check(user_id="test-user", cart_data=cart_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["deleted_products"] == []
        assert response.data["price_mismatches"] == []

    def test_cart_with_deleted_and_price_mismatch(self):
        mock_cart = MockCartService()
        mock_cart.mock_response = {
            "total": 8610,
            "deleted_products": ["Product X"],
            "price_mismatches": [
                {
                    "product_id": 1,
                    "name": "Test Product",
                    "old_price": 10,
                    "new_price": 1000
                }
            ],
            "updated_cart": {
                "products": [
                    {"product_id": 1, "name": "Test Product", "price": 1000, "bonus": 100, "quantity": 1}
                ]
            },
            "add_bonuses": 100
        }

        service = CheckCartService(cart_service=mock_cart)

        cart_data = {
            "total": 8610,
            "products": [
                {"product_id": 1, "name": "Test Product", "price": 10, "image": [], "quantity": 1},
                {"product_id": 999, "name": "Product X", "price": 500, "image": [], "quantity": 1}
            ]
        }

        response = service.check(user_id="test-user", cart_data=cart_data)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["deleted_products"] == ["Product X"]
        assert response.data["price_mismatches"][0]["old_price"] == 10
        assert response.data["price_mismatches"][0]["new_price"] == 1000
