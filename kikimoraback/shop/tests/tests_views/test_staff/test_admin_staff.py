from django.urls import reverse

import pytest


@pytest.mark.django_db
class TestAdminStaff:
    def test_get_all_staff(self, client, admin_user, admin_user2, regular_user):
        client.force_login(admin_user)
        url = reverse("staff")
        response = client.get(url)

        assert response.status_code == 200
        admins = response.context["admins"]
        # В queryset должны быть только сотрудники
        assert all(admin["is_staff"] for admin in admins)
        emails = [admin["email"] for admin in admins]
        assert admin_user.email in emails
        assert admin_user.email in emails
        assert regular_user.email not in emails

    def test_post_search_by_email(self, client, admin_user, admin_user2):
        client.force_login(admin_user)
        url = reverse("staff")

        data = {"email": admin_user2.email, "fio": "", "phone": ""}
        response = client.post(url, data)

        assert response.status_code == 200
        admins = response.context["admins"]
        assert len(admins) == 1
        assert admins[0]["email"] == admin_user2.email

    def test_access_denied_for_non_staff(self, client, regular_user):
        client.force_login(regular_user)
        url = reverse("staff")
        response = client.get(url)
        assert response.status_code == 302

    def test_access_denied_for_anonymous(self, client):
        url = reverse("staff")
        response = client.get(url)
        assert response.status_code == 302
