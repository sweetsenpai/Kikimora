from django.contrib.messages import get_messages
from django.urls import reverse

import pytest


@pytest.mark.django_db
class TestAdminLogin:

    def test_admin_login_success(self, client, admin_user):
        response = client.post(
            reverse("admin_login"),
            {
                "email": admin_user.email,
                "password": "password123",
            },
        )
        assert response.status_code == 302
        assert response.url == reverse("admin_home")

    def test_regular_user_login_denied(self, client, regular_user):
        response = client.post(
            reverse("admin_login"),
            {
                "email": regular_user.email,
                "password": "password123",
            },
        )
        assert response.status_code == 200
        messages = [m.message for m in get_messages(response.wsgi_request)]
        assert "У вас нет доступа к административной панели." in messages

    def test_login_with_invalid_credentials(self, client, admin_user):
        response = client.post(
            reverse("admin_login"),
            {"email": admin_user.email, "password": "not_a_password"},
        )
        assert response.status_code == 200
        messages = [m.message for m in get_messages(response.wsgi_request)]
        assert "Неправильный email или пароль." in messages
