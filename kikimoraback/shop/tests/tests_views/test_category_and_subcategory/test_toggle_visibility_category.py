from django.urls import reverse

import pytest

from shop.models import Category


@pytest.mark.django_db
class TestToggleVisibilityCategory:
    def test_valid_toggle(self, client, admin_user, category):
        client.force_login(admin_user)
        category_visability_before = category.visibility
        url = reverse(
            "change_visability_category", kwargs={"category_id": category.category_id}
        )
        response = client.post(url)

        assert response.status_code == 200
        updated_category = Category.objects.get(category_id=category.category_id)
        assert updated_category.visibility != category_visability_before

    def test_toggle_get_method(self, client, admin_user, category):
        client.force_login(admin_user)
        category_visability_before = category.visibility
        url = reverse(
            "change_visability_category", kwargs={"category_id": category.category_id}
        )
        response = client.get(url)

        assert response.status_code == 400
        updated_category = Category.objects.get(category_id=category.category_id)
        assert updated_category.visibility == category_visability_before

    def test_toogle_non_existing_category(self, client, admin_user, category):
        client.force_login(admin_user)
        category_visability_before = category.visibility
        url = reverse("change_visability_category", kwargs={"category_id": 6000})
        response = client.post(url)

        assert response.status_code == 404

    def test_toogle_category_by_not_admin(self, client, regular_user, category):
        client.force_login(regular_user)
        category_visability_before = category.visibility
        url = reverse(
            "change_visability_category", kwargs={"category_id": category.category_id}
        )
        response = client.post(url)

        assert response.status_code == 302
        updated_category = Category.objects.get(category_id=category.category_id)
        assert updated_category.visibility == category_visability_before
