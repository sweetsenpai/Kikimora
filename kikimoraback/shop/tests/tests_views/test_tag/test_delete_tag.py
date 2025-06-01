from django.urls import reverse

import pytest

from shop.models import ProductTag


class TestAdminDeleteTag:
    def test_valid_delete_tag(self, client, admin_user, tags):
        client.force_login(admin_user)
        tag = tags[0]

        url = reverse("delete_tag", kwargs={"tag_id": tag.tag_id})

        response = client.post(url)

        db_tag = ProductTag.objects.filter(tag_id=tag.tag_id).first()

        assert response.url == reverse("tags")
        assert db_tag is None

    def test_invalid_delete_tag(self, client, admin_user):
        client.force_login(admin_user)

        url = reverse("delete_tag", kwargs={"tag_id": 6000})

        response = client.post(url)

        assert response.status_code == 404

    def test_valid_delete_tag_not_admin(self, client, regular_user, tags):
        client.force_login(regular_user)
        tag = tags[0]

        url = reverse("delete_tag", kwargs={"tag_id": tag.tag_id})

        response = client.post(url)

        db_tag = ProductTag.objects.filter(tag_id=tag.tag_id).first()

        assert response.url == reverse("admin_login")
        assert db_tag is not None
