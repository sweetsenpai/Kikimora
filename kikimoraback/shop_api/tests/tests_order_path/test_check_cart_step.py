from rest_framework import status
from rest_framework.response import Response
from unittest.mock import MagicMock
import pytest

from shop_api.services.order_path_services.check_cart_service import CheckCartService


class MockCartService:
    def check_cart_data(self, front_data, user_id):
        return self.mock_response

    def sync_cart_data(self, user_id, front_cart_data):
        self.synced_data = front_cart_data


@pytest.mark.django_db
class TestCheckCartService:

    def test_empty_cart(self):
        mock_cart = MagicMock()
        service = CheckCartService(cart_service=mock_cart)

        # Данные пустой корзины
        response = service.check(user_id="test-user", cart_data={})

        # Проверяем, что ответ правильный
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["error"] == "В корзине ничего нет"

        # Проверяем, что метод check_cart_data не был вызван
        mock_cart.check_cart_data.assert_not_called()

    def test_valid_cart(self):
        mock_cart = MagicMock()
        mock_cart.check_cart_data.return_value = {
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

        # Проверка вызова sync_cart_data
        mock_cart.sync_cart_data.assert_called_once()

    def test_cart_with_deleted_and_price_mismatch(self):
        mock_cart = MagicMock()
        mock_cart.check_cart_data.return_value = {
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

        # Проверка вызова sync_cart_data
        mock_cart.sync_cart_data.assert_called_once()

    def test_sync_cart_called(self):
        # Создаём моковый объект для Cart
        mock_cart = MagicMock()

        # Указываем, что будет возвращать check_cart_data при вызове
        mock_cart.check_cart_data.return_value = {
            "total": 8610,
            "deleted_products": [],
            "price_mismatches": [],
            "updated_cart": {
                "products": [
                    {
                        "product_id": 1,
                        "name": "Test Product",
                        "price": 1000,
                        "bonus": 100,
                        "quantity": 1,
                    }
                ]
            },
            "add_bonuses": 100,
        }

        # Создаём экземпляр сервиса
        service = CheckCartService(cart_service=mock_cart)

        # Пример данных корзины, которые будем передавать в метод check
        cart_data = {
            "total": 8610,
            "products": [
                {
                    "product_id": 1,
                    "name": "Test Product",
                    "price": 1000,
                    "image": [],
                    "quantity": 1,
                }
            ],
        }

        # Вызов метода
        service.check(user_id="test-user", cart_data=cart_data)

        # Проверка, что метод sync_cart_data был вызван один раз
        mock_cart.sync_cart_data.assert_called_once()

        # Проверка, что метод sync_cart_data был вызван с правильными аргументами
        expected_data = {
            "total": 8610,
            "products": [
                {
                    "product_id": 1,
                    "name": "Test Product",
                    "price": 1000,
                    "bonus": 100,
                    "quantity": 1,
                }
            ],
            "add_bonuses": 100,
        }

        # Проверяем, что переданные данные совпадают с ожидаемыми
        mock_cart.sync_cart_data.assert_called_with(
            user_id="test-user", front_cart_data=expected_data
        )