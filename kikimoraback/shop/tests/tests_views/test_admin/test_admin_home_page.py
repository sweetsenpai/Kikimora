from django.urls import reverse

import pytest


@pytest.mark.django_db
class TestAdminHomePage:

    def test_admin_access(self, client, admin_user):
        client.force_login(admin_user)
        response = client.get(reverse("admin_home"))
        assert response.status_code == 200

    def test_not_admin_access(self, client, regular_user):
        client.force_login(regular_user)
        response = client.get(reverse("admin_home"))
        assert response.status_code == 302
        assert response.url == reverse("admin_login")

    def test_anonymous_access(self, client):
        response = client.get(reverse("admin_home"))
        assert response.status_code == 302
        assert response.url == reverse("admin_login")
