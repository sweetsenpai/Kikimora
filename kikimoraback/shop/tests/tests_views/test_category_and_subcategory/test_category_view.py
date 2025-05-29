from django.urls import reverse

import pytest

from shop.models import Category


@pytest.mark.django_db
class TestAdminCategoryView:
    def test_admin_get_page_category(self, client, admin_user, category):
        client.force_login(admin_user)
        url = reverse("admin_category_view")
        response = client.get(url)

        assert response.status_code == 200
        assert list(response.context["categories"]) == list(Category.objects.all())

    def test_not_admin_get_page_category(self, client, regular_user):
        client.force_login(regular_user)
        url = reverse("admin_category_view")
        response = client.get(url)

        assert response.status_code == 302
        assert response.url == reverse("admin_login")
