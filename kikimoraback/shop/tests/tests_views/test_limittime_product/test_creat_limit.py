from django.urls import reverse
from django.utils import timezone

import pytest

from shop.models import LimitTimeProduct


class TestAdminLimitTimeProductForm:
    def test_valid_creat_limit(self, client, admin_user, products_set_1):
        client.force_login(admin_user)
        product = products_set_1[0]
        url = reverse("day_products_form", kwargs={"product_id": product.product_id})

        valid_data = {
            "ammount": 5,
            "price": 200,
            "due": timezone.now() + timezone.timedelta(days=10),
        }

        empty_db = LimitTimeProduct.objects.all()

        client.post(url, data=valid_data)
        non_empty_db = LimitTimeProduct.objects.all()

        assert empty_db != non_empty_db

    def test_invalid_creat_limit(self, client, admin_user, products_set_1):
        client.force_login(admin_user)
        product = products_set_1[0]
        url = reverse("day_products_form", kwargs={"product_id": product.product_id})

        valid_data = {
            "ammount": "",
            "price": "",
            "due": timezone.now() + timezone.timedelta(days=10),
        }

        empty_db = LimitTimeProduct.objects.all()

        client.post(url, data=valid_data)
        non_empty_db = LimitTimeProduct.objects.all()

        assert set(empty_db) == set(non_empty_db)

    def test_valid_creat_limit_non_admin(self, client, regular_user, products_set_1):
        client.force_login(regular_user)
        product = products_set_1[0]
        url = reverse("day_products_form", kwargs={"product_id": product.product_id})

        valid_data = {
            "ammount": 5,
            "price": 200,
            "due": timezone.now() + timezone.timedelta(days=10),
        }

        empty_db = LimitTimeProduct.objects.all()

        response = client.post(url, data=valid_data)
        non_empty_db = LimitTimeProduct.objects.all()

        assert set(empty_db) == set(non_empty_db)
        assert response.url == reverse("admin_login")
