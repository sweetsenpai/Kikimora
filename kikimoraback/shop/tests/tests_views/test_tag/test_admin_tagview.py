from django.urls import reverse

import pytest


@pytest.mark.django_db
class TestAdminTagView:
    def test_admin_get_tags(self, client, tags, admin_user):
        client.force_login(admin_user)
        response = client.get(reverse("tags"))

        assert response.status_code == 200
        assert list(response.context["tags"]) == list(tags)

    def test_non_admin_get_tags(self, client, tags, regular_user):
        client.force_login(regular_user)
        response = client.get(reverse("tags"))

        assert response.status_code == 302
        assert response.url == reverse("admin_login")
