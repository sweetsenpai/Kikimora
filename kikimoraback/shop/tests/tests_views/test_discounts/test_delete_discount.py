from django.urls import reverse

import pytest

from shop.models import Discount


class TestDeleteDiscount:
    def test_valid_discount_delete(self, client, admin_user, discount_subcategory_recipe):
        client.force_login(admin_user)
        url = reverse(
            "delete_discount", kwargs={"discount_id": discount_subcategory_recipe.discount_id}
        )

        response = client.post(url)
        discount_after_delete = Discount.objects.filter(
            discount_id=discount_subcategory_recipe.discount_id
        ).first()

        assert response.status_code == 200
        assert discount_after_delete is None

    def test_invalid_discount_delete(self, client, admin_user):
        client.force_login(admin_user)
        url = reverse("delete_discount", kwargs={"discount_id": 6000})

        response = client.post(url)

        assert response.status_code == 404

    def test_valid_discount_delete_non_admin(
        self, client, regular_user, discount_subcategory_recipe
    ):
        client.force_login(regular_user)
        url = reverse(
            "delete_discount", kwargs={"discount_id": discount_subcategory_recipe.discount_id}
        )

        response = client.post(url)
        discount_after_delete = Discount.objects.filter(
            discount_id=discount_subcategory_recipe.discount_id
        ).first()

        assert response.status_code == 302
        assert discount_after_delete is not None
