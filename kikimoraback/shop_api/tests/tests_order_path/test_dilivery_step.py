import json
import os
import uuid
from unittest.mock import Mock, patch

from django.contrib.auth.models import AnonymousUser
from django.http import JsonResponse
from django.test import RequestFactory, override_settings

from rest_framework import status
from rest_framework.response import Response

import pytest

from shop_api.api_views.payment.order_path_views import OrderPath


@pytest.fixture
def request_factory():
    return RequestFactory()


@pytest.fixture
def anonymous_user():
    return AnonymousUser()


@pytest.fixture
def mock_cart_service():
    cart_service = Mock()
    cart_service.ping.return_value = True
    return cart_service


@pytest.fixture
def mock_order_service():
    order_service = Mock()
    order_service.ping.return_value = True
    return order_service


@patch.dict(os.environ, {"YANDEX_API_TOKEN": "None"}, clear=True)
@patch("shop_api.api_views.payment.order_path_views.Cart")
@patch("shop_api.api_views.payment.order_path_views.Order")
@patch("shop_api.api_views.payment.order_path_views.requests.post")
def test_delivery_step_success(
    mock_requests_post,
    mock_order,
    mock_cart,
    request_factory,
    anonymous_user,
    mock_cart_service,
    mock_order_service,
):
    # Arrange
    mock_cart.return_value = mock_cart_service
    mock_order.return_value = mock_order_service

    mock_response = Mock()
    mock_response.ok = True
    mock_response.status_code = 200
    mock_response.json.return_value = {"distance_meters": 3000, "price": 500.0}
    mock_requests_post.return_value = mock_response

    user_id = str(uuid.uuid4())
    delivery_data = {"address": "ул. Тестовая, д.1"}
    data = {"steps": ["delivery_step"], "deliveryData": delivery_data}

    request = request_factory.post("/order", data, content_type="application/json", timeout=10)
    request.user = anonymous_user
    request.COOKIES = {"user_id": user_id}

    view = OrderPath.as_view()

    # Act
    response = view(request)
    response.render()
    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.data == {
        "price": 600,
        "distance_meters": 3000,
    }
    mock_requests_post.assert_called_once_with(
        "https://b2b.taxi.yandex.net/b2b/cargo/integration/v2/check-price",
        headers={"Authorization": "Bearer None", "Accept-Language": "ru/ru"},
        json={
            "route_points": [
                {"fullname": "Санкт-Петербург, 11-я Красноармейская улица, 11"},
                {"fullname": "Санкт-Петербург, ул. Тестовая, д.1"},
            ]
        },
        timeout=10,
    )


@patch.dict(os.environ, {"YANDEX_API_TOKEN": "None"}, clear=True)
@patch("shop_api.api_views.payment.order_path_views.Cart")
@patch("shop_api.api_views.payment.order_path_views.Order")
@patch("shop_api.api_views.payment.order_path_views.requests.post")
def test_delivery_step_missing_address(
    mock_requests_post,
    mock_order,
    mock_cart,
    request_factory,
    anonymous_user,
    mock_cart_service,
    mock_order_service,
):
    # Arrange
    mock_cart.return_value = mock_cart_service
    mock_order.return_value = mock_order_service

    user_id = str(uuid.uuid4())
    data = {"steps": ["delivery_step"], "deliveryData": {}}

    request = request_factory.post("/order", data=json.dumps(data), content_type="application/json")
    request.user = anonymous_user
    request.COOKIES = {"user_id": user_id}

    view = OrderPath.as_view()

    # Act
    response = view(request)
    response.render()
    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {"error": "Не передан адрес для расчета доставки."}
    mock_requests_post.assert_not_called()


@patch.dict(os.environ, {"YANDEX_API_TOKEN": "None"}, clear=True)
@patch("shop_api.api_views.payment.order_path_views.Cart")
@patch("shop_api.api_views.payment.order_path_views.Order")
@patch("shop_api.api_views.payment.order_path_views.requests.post")
def test_delivery_step_yandex_api_error(
    mock_requests_post,
    mock_order,
    mock_cart,
    request_factory,
    anonymous_user,
    mock_cart_service,
    mock_order_service,
):
    # Arrange
    mock_cart.return_value = mock_cart_service
    mock_order.return_value = mock_order_service

    mock_response = Mock()
    mock_response.ok = False
    mock_response.status_code = 400
    mock_response.json.return_value = {"error": "Invalid address"}
    mock_requests_post.return_value = mock_response

    user_id = str(uuid.uuid4())
    delivery_data = {"address": "Неправильный адрес"}
    data = {"steps": ["delivery_step"], "deliveryData": delivery_data}

    request = request_factory.post("/order", data, content_type="application/json")
    request.user = anonymous_user
    request.COOKIES = {"user_id": user_id}

    view = OrderPath.as_view()

    # Act
    response = view(request)
    response.render()
    # Assert
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data == {
        "error": "Не удалось рассчитать стоимость доставки. Проверьте правильность введенного адреса."
    }
    mock_requests_post.assert_called_once()
