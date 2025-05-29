from django.urls import reverse

from rest_framework.fields import empty

import pytest

from shop.models import ProductTag


@pytest.mark.django_db
class TestNewTag:
    def test_valid_new_tag(self, client, admin_user):
        client.force_login(admin_user)

        test_text = "Test Tag"

        response = client.post(reverse("new-tag"), {"text": test_text})

        new_tag = ProductTag.objects.get(text=test_text)

        assert response.status_code == 302
        assert response.url == reverse("tags")
        assert new_tag is not None

    def test_invalid_new_tag(self, client, admin_user):
        client.force_login(admin_user)

        test_text = ""

        response = client.post(reverse("new-tag"), {"text": test_text})

        tags = list(ProductTag.objects.all())

        assert response.status_code == 200
        assert len(tags) == 0

    def test_valid_new_tag_not_admin(self, client, regular_user):
        client.force_login(regular_user)
        test_text = "Test Tag"

        response = client.post(reverse("new-tag"), {"text": test_text})

        new_tag = list(ProductTag.objects.all())

        assert response.status_code == 302
        assert response.url == reverse("admin_login")
        assert len(new_tag) == 0
