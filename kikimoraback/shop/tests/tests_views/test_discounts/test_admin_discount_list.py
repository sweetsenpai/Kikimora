from django.urls import reverse

import pytest


class TestAdminDiscountListView:
    def test_get_valid_discount_view(
        self,
        client,
        admin_user,
        discounts_product_fixture,
        discounts_category_fixture,
        discount_subcategory_recipe,
    ):
        client.force_login(admin_user)
        response = client.get(reverse("discounts"))

        assert response.status_code == 200
        assert len(response.context["discounts"]) == 3

    def test_get_discount_view_non_admin(
        self,
        client,
        regular_user,
        discounts_product_fixture,
        discounts_category_fixture,
        discount_subcategory_recipe,
    ):
        client.force_login(regular_user)
        response = client.get(reverse("discounts"))

        assert response.status_code == 302
        assert response.url == reverse("admin_login")
