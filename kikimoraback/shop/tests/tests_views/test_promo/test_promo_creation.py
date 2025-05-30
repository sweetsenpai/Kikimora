from django.urls import reverse
from django.utils import timezone

import pytest

from shop.models import PromoSystem


class TestAdminNewPromo:
    def test_valid_promo_creation(self, client, admin_user):
        client.force_login(admin_user)

        url = reverse("new_promo")

        valid_data = {
            "description": "test_promo",
            "code": "12345TEST",
            "type": "delivery",
            "start": timezone.now(),
            "end": timezone.now() + timezone.timedelta(days=30),
            "promo_product": "",
            "min_sum": "",
            "amount": "",
            "procentage": "",
            "one_time": "",
        }

        response = client.post(url, data=valid_data)

        new_promo = PromoSystem.objects.get(code=valid_data["code"])

        assert response.url == reverse("promocods")
        assert new_promo is not None
        assert new_promo.type == valid_data["type"]
        assert new_promo.start == valid_data["start"]
        assert new_promo.end == valid_data["end"]

    def test_invalid_promo_creation(self, client, admin_user):
        client.force_login(admin_user)

        url = reverse("new_promo")

        valid_data = {
            "description": "test_promo",
            "code": "12345TEST",
            "type": "delivery",
            "start": "1",
            "end": "",
            "promo_product": "",
            "min_sum": "",
            "amount": "",
            "procentage": "",
            "one_time": "",
        }

        response = client.post(url, data=valid_data)
        new_promo = PromoSystem.objects.filter(code=valid_data["code"]).first()

        assert new_promo is None

    def test_valid_promo_creation_non_admin(self, client, regular_user):
        client.force_login(regular_user)

        url = reverse("new_promo")

        valid_data = {
            "description": "test_promo",
            "code": "12345TEST",
            "type": "delivery",
            "start": timezone.now(),
            "end": timezone.now() + timezone.timedelta(days=30),
            "promo_product": "",
            "min_sum": "",
            "amount": "",
            "procentage": "",
            "one_time": "",
        }

        response = client.post(url, data=valid_data)
        new_promo = PromoSystem.objects.filter(code=valid_data["code"]).first()

        assert response.url == reverse("admin_login")
        assert new_promo is None
