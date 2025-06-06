import json
from unittest.mock import MagicMock

from rest_framework import status

import pytest

from shop_api.services.order_path_services.payment_service import PaymentService


@pytest.fixture
def mock_cart():
    mock = MagicMock()
    mock.get_cart_data.return_value = {"delivery_data": {"type": "pickup"}}
    return mock


@pytest.fixture
def mock_order():
    mock = MagicMock()
    mock.get_neworder_num.return_value = "ORDER-123"
    return mock


@pytest.fixture
def mock_gateway():
    mock = MagicMock()
    mock.send_payment_request.return_value = json.dumps(
        {
            "id": "PAYMENT-ID",
            "confirmation": {"confirmation_url": "https://pay.example.com/redirect"},
        }
    )
    return mock


@pytest.fixture
def payment_service(mock_cart, mock_order, mock_gateway):
    return PaymentService(mock_cart, mock_order, mock_gateway)


def test_payment_success(payment_service, mock_cart):
    user_id = "user-1"
    response = payment_service.process_payment(
        user_id=user_id,
        user_data={"name": "Test"},
        bonuses=0,
    )

    assert response.status_code == status.HTTP_302_FOUND
    assert "redirect_url" in response.data
    mock_cart.delete_cart.assert_called_once_with(user_id="user-1")


from shop.services.caches import UserBonusSystem


def test_bonus_deduction_failure(payment_service, mock_cart, monkeypatch):
    monkeypatch.setattr(
        UserBonusSystem,
        "deduct_bonuses",
        lambda *args, **kwargs: (_ for _ in ()).throw(Exception("fail")),
    )

    response = payment_service.process_payment(user_id="user-2", user_data={}, bonuses=100)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "error" in response.data


def test_payment_gateway_returns_none(payment_service, mock_gateway):
    mock_gateway.send_payment_request.return_value = "{}"

    response = payment_service.process_payment(user_id="user-3", user_data={}, bonuses=0)

    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert "error" in response.data
