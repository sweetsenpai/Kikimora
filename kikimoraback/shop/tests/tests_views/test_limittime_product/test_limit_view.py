from django.urls import reverse

import pytest


class TestLimitView:
    def test_get_limit_view(self, client, admin_user, limit_time_fixture):
        client.force_login(admin_user)

        response = client.get(reverse("day_products"))

        assert response.status_code == 200
        assert set(response.context["limit_products"]) == set(limit_time_fixture)

    def test_get_limit_view_non_admin(self, client, regular_user, limit_time_fixture):
        client.force_login(regular_user)

        response = client.get(reverse("day_products"))

        assert response.url == reverse("admin_login")
