from django.urls import reverse
from django.utils import timezone

import pytest

from shop.models import Discount


class TestAdminNewDiscount:
    def test_vaild_creation_discount(self, client, admin_user, products_set_1):
        client.force_login(admin_user)

        url = reverse("new_discount")

        new_discount_data = {
            "discount_type": "amount",
            "value": 100,
            "description": "",
            "start": timezone.now(),
            "end": timezone.now() + timezone.timedelta(days=10),
            "product": products_set_1[0].product_id,
        }

        responce = client.post(url, data=new_discount_data)
        discount = Discount.objects.filter(product=products_set_1[0].product_id).first()
        assert responce.url == reverse("discounts")
        assert discount is not None

    def test_invalid_creation_discount(self, client, admin_user):
        client.force_login(admin_user)

        url = reverse("new_discount")

        new_discount_data = {
            "discount_type": "amount",
            "value": 100,
            "description": "",
            "start": timezone.now(),
            "end": timezone.now() + timezone.timedelta(days=10),
            "product": 6000,
        }

        client.post(url, data=new_discount_data)
        discount = Discount.objects.filter(product=6000).first()
        assert discount is None

    def test_creat_discount_non_admin(self, client, regular_user, products_set_1):
        client.force_login(regular_user)

        url = reverse("new_discount")

        new_discount_data = {
            "discount_type": "amount",
            "value": 100,
            "description": "",
            "start": timezone.now(),
            "end": timezone.now() + timezone.timedelta(days=10),
            "product": products_set_1[0].product_id,
        }

        responce = client.post(url, data=new_discount_data)
        discount = Discount.objects.filter(product=products_set_1[0].product_id).first()
        assert responce.url == reverse("admin_login")
        assert discount is None
