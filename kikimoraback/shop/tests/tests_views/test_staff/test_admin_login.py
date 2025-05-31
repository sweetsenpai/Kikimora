from django.contrib.messages import get_messages
from django.urls import reverse

import pytest


@pytest.mark.django_db
class TestAdminLogin:

    def test_admin_login_success(self, client, admin_user):
        response = client.post(
            reverse("admin_login"),
            {
                "username": admin_user.email,
                "password": "password123",
            },
        )
        assert response.url == reverse("admin_home")
        assert response.wsgi_request.user.is_authenticated
        assert response.wsgi_request.user == admin_user

    def test_regular_user_login_denied(self, client, regular_user):
        response = client.post(
            reverse("admin_login"),
            {
                "username": regular_user.email,
                "password": "password123",
            },
        )
        assert response.status_code == 200
        assert not response.wsgi_request.user.is_authenticated

    def test_login_with_invalid_credentials(self, client, admin_user):
        response = client.post(
            reverse("admin_login"),
            {"username": admin_user.email, "password": "not_a_password"},
        )
        assert response.status_code == 200
        assert not response.wsgi_request.user.is_authenticated
