from django.urls import reverse

import pytest

from shop.models import Subcategory


@pytest.mark.django_db
class TestToggleVisibilityCategory:
    def test_valid_toggle(self, client, admin_user, subcategories):
        client.force_login(admin_user)
        subcategory = subcategories[0]
        subcategory_visability_before = subcategory.visibility
        url = reverse(
            "change_visibility_subcat",
            kwargs={"subcategory_id": subcategory.subcategory_id},
        )
        response = client.post(url)

        assert response.status_code == 200
        updated_subcategory = Subcategory.objects.get(subcategory_id=subcategory.subcategory_id)
        assert updated_subcategory.visibility != subcategory_visability_before

    def test_toggle_get_method_subcategory(self, client, admin_user, subcategories):
        client.force_login(admin_user)
        subcategory = subcategories[0]
        subcategory_visability_before = subcategory.visibility
        url = reverse(
            "change_visibility_subcat",
            kwargs={"subcategory_id": subcategory.subcategory_id},
        )
        response = client.get(url)

        assert response.status_code == 400
        updated_subcategory = Subcategory.objects.get(subcategory_id=subcategory.subcategory_id)
        assert updated_subcategory.visibility == subcategory_visability_before

    def test_toogle_non_existing_subcategory(self, client, admin_user, subcategories):
        client.force_login(admin_user)
        url = reverse("change_visibility_subcat", kwargs={"subcategory_id": 6000})
        response = client.post(url)

        assert response.status_code == 404

    def test_toogle_category_by_not_admin(self, client, regular_user, subcategories):
        subcategory = subcategories[0]
        subcategory_visability_before = subcategory.visibility
        url = reverse(
            "change_visibility_subcat",
            kwargs={"subcategory_id": subcategory.subcategory_id},
        )
        response = client.post(url)

        assert response.status_code == 302
        updated_subcategory = Subcategory.objects.get(subcategory_id=subcategory.subcategory_id)
        assert updated_subcategory.visibility == subcategory_visability_before
