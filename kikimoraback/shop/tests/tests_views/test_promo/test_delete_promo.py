from django.urls import reverse

import pytest

from shop.models import PromoSystem


class TestDeletePromo:
    def test_delete_promo_valid(self, client, admin_user, promo_fixtures):
        client.force_login(admin_user)

        promocode = promo_fixtures[0]

        url = reverse("promocod_delete", kwargs={"promo_id": promocode.promo_id})
        response = client.post(url)

        promo_deleted = PromoSystem.objects.filter(promo_id=promocode.promo_id).first()

        assert promo_deleted is None

    def test_delete_promo_invalid(self, client, admin_user):
        client.force_login(admin_user)
        url = reverse("promocod_delete", kwargs={"promo_id": 6000})
        response = client.post(url)
        assert response.status_code == 404

    def test_delete_promo_valid_non_admin(self, client, regular_user, promo_fixtures):
        client.force_login(regular_user)

        promocode = promo_fixtures[0]

        url = reverse("promocod_delete", kwargs={"promo_id": promocode.promo_id})
        response = client.post(url)

        promo_deleted = PromoSystem.objects.filter(promo_id=promocode.promo_id).first()

        assert response.status_code == 302
        assert promo_deleted is not None
