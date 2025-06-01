from django.urls import reverse

import pytest


class TestAdminPromocodeListView:
    def test_get_promocode(self, client, admin_user, promo_fixtures):
        client.force_login(admin_user)

        response = client.get(reverse("promocods"))

        assert response.status_code == 200
        assert set(response.context["promocodes"]) == set(promo_fixtures)

    def test_get_promocode_non_admin(self, client, regular_user, promo_fixtures):
        client.force_login(regular_user)
        response = client.get(reverse("promocods"))

        assert response.status_code == 302
        assert response.url == reverse("admin_login")
