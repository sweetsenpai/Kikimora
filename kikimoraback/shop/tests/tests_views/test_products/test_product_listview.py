from django.urls import reverse

import pytest

from shop.models import Product


@pytest.mark.django_db
class TestAdminProdactListView:
    def test_get_productlist(
        self, client, admin_user, products_set_1, subcategories, category
    ):
        client.force_login(admin_user)
        url = reverse(
            "product_list",
            kwargs={
                "category_id": category.category_id,
                "subcategory_id": subcategories[0].subcategory_id,
            },
        )

        response = client.get(url)

        assert response.status_code == 200

        products = Product.objects.filter(subcategory=subcategories[0])

        assert list(response.context["products"]) == list(products)

    def test_search_productlist(
        self, client, admin_user, products_set_1, subcategories, category
    ):
        client.force_login(admin_user)
        product = products_set_1[0]
        url = reverse(
            "product_list",
            kwargs={
                "category_id": category.category_id,
                "subcategory_id": subcategories[0].subcategory_id,
            },
        )

        response = client.post(url, {"name": product.name})

        assert response.status_code == 200
        assert response.context["products"][0].name == product.name

    def test_nonexisting_product(self, client, admin_user, subcategories, category):
        client.force_login(admin_user)
        url = reverse(
            "product_list",
            kwargs={
                "category_id": category.category_id,
                "subcategory_id": subcategories[0].subcategory_id,
            },
        )

        response = client.post(url, {"name": "Total Random Name for a Product"})

        assert response.status_code == 200
        assert len(response.context["products"]) == 0

    def test_not_admin_get_productlist(
        self, client, regular_user, products_set_1, subcategories, category
    ):
        client.force_login(regular_user)
        url = reverse(
            "product_list",
            kwargs={
                "category_id": category.category_id,
                "subcategory_id": subcategories[0].subcategory_id,
            },
        )

        response = client.get(url)

        assert response.status_code == 302
        assert response.url == reverse("admin_login")
