from django.urls import reverse

import pytest

from shop.models import Product


@pytest.mark.django_db
class TestProductUpdateView:
    def test_valid_product_update(self, client, admin_user, products_set_1):
        client.force_login(admin_user)
        product = products_set_1[0]
        url = reverse("product_update", kwargs={"product_id": product.product_id})

        data = {
            "name": "Updated Name",
            "description": product.description or "Default description",
            "price": product.price,
            "weight": 100,
            "bonus": product.bonus,
            "tag": product.tag.pk if product.tag else "",
        }

        client.post(url, data)

        updated = Product.objects.get(product_id=product.product_id)

        assert updated.name == "Updated Name"
        assert updated.price == product.price
        assert updated.weight == 100
        assert updated.bonus == product.bonus

    def test_invalid_product_update(self, client, admin_user, products_set_1):
        client.force_login(admin_user)
        product = products_set_1[0]
        url = reverse("product_update", kwargs={"product_id": product.product_id})

        original_data = {
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "weight": product.weight,
            "bonus": product.bonus,
            "tag": product.tag.pk if product.tag else "",
        }

        # создаём копию с невалидной ценой
        invalid_data = original_data.copy()
        invalid_data["price"] = ""

        response = client.post(url, invalid_data)
        updated = Product.objects.get(product_id=product.product_id)
        assert updated.name == product.name
        assert updated.description == product.description
        assert updated.price == product.price

    def test_not_admin_product_update(self, client, regular_user, products_set_1):
        product = products_set_1[0]
        url = reverse("product_update", kwargs={"product_id": product.product_id})

        data = {
            "name": "Updated Name",
            "description": product.description or "Default description",
            "price": product.price,
            "weight": 100,
            "bonus": product.bonus,
            "tag": product.tag.pk if product.tag else "",
        }

        response = client.post(url, data)

        updated = Product.objects.get(product_id=product.product_id)

        assert updated.name == product.name
        assert updated.weight == product.weight
        assert response.url == reverse("admin_login")
