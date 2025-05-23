from unittest.mock import patch

from rest_framework.response import Response
from rest_framework.test import APIClient

import pytest


@pytest.mark.django_db
class TestOrderPath:
    def setup_method(self):
        self.client = APIClient()
        base_path = "shop_api.api_views.payment.order_path_views"

        patcher_cart = patch(f"{base_path}.Cart")
        patcher_order = patch(f"{base_path}.Order")
        patcher_check = patch(f"{base_path}.CheckCartService")
        patcher_delivery = patch(f"{base_path}.DeliveryService")
        patcher_payment = patch(f"{base_path}.PaymentService")
        patcher_user = patch(f"{base_path}.UserIdentifierService")

        self.mock_cart = patcher_cart.start()
        self.mock_order = patcher_order.start()
        self.mock_check_cart = patcher_check.start()
        self.mock_delivery = patcher_delivery.start()
        self.mock_payment = patcher_payment.start()
        self.mock_user_service = patcher_user.start()

        self.patchers = [
            patcher_cart,
            patcher_order,
            patcher_check,
            patcher_delivery,
            patcher_payment,
            patcher_user,
        ]

        # Пинги
        self.mock_cart.return_value.ping.return_value = True
        self.mock_order.return_value.ping.return_value = True

        # user_id
        self.mock_user_service.return_value.get_or_create_user_id.return_value = (
            "user-123",
            None,
        )

    def teardown_method(self):
        for patcher in self.patchers:
            patcher.stop()

    def base_payload(self, steps=None):
        return {
            "steps": steps or ["payment_step"],
            "cart": {
                "total": 2400,
                "products": [
                    {
                        "product_id": 483174435,
                        "name": "15 оттенков весны",
                        "price": 2400,
                        "image": [],
                        "quantity": 1,
                    }
                ],
            },
            "userData": {
                "fio": "Sasha1",
                "phone": "+79118468177",
                "email": "chcolatemilk00@gmail.com",
            },
            "deliveryData": {
                "deliveryMethod": "Доставка",
                "address": "8-ая Красноармейская, 14",
                "street": "8-ая Красноармейская",
                "houseNumber": "14",
                "appartmentNumber": "13",
                "date": "2025-04-18",
                "time": "15:00-18:00",
                "deliveryCost": None,
            },
            "usedBonus": 720,
            "comment": "",
        }

    def test_success_payment_path(self):
        self.mock_check_cart.return_value.check.return_value = Response(
            {
                "total": 2400,
                "deleted_products": [],
                "price_mismatches": [],
                "updated_cart": {
                    "products": [
                        {
                            "product_id": 483174435,
                            "name": "15 оттенков весны",
                            "price": 2400,
                            "bonus": 200,
                            "quantity": 1,
                        }
                    ]
                },
                "add_bonuses": 200,
            },
            status=200,
        )

        self.mock_delivery.return_value.calculate.return_value = Response(
            {"delivery_price": 500}, status=200
        )

        self.mock_payment.return_value.process_payment.return_value = Response(
            {"payment_id": "123", "status": "success"}, status=200
        )

        response = self.client.post(
            "/api/v1/orderpath", self.base_payload(), format="json"
        )

        assert response.status_code == 200
        assert response.data["status"] == "success"
        assert response.data["payment_id"] == "123"

    def test_empty_steps_returns_400(self):
        payload = self.base_payload(steps=[])
        response = self.client.post("/api/v1/orderpath", payload, format="json")
        assert response.status_code == 400
        assert "steps" in response.data
