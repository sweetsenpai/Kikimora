from django.urls import reverse
from django.contrib.auth import get_user_model
import pytest


class TestAdminCreateAdmin:
    def test_create_new_admin_valid_data(self, client, admin_user):
        client.force_login(admin_user)
        url = reverse("admin_create")
        response = client.post(url,{
            "email": "admin3@example.com",
            "phone": "+79110000004",
            "user_fio": "Test New Admin",
            "is_superuser": True,
        })

        assert response.status_code == 200
        user = get_user_model().objects.get(phone="+79110000004")
        assert user.user_fio == "Test New Admin"

    def test_create_new_admin_no_valid_data(self, client, admin_user):
        client.force_login(admin_user)
        url = reverse("admin_create")
        response = client.post(url, {
            "email": "admin3@example.com",
            "phone": "",
            "user_fio": "Test New Admin",
            "is_superuser": True,
        })

        assert response.status_code == 200

    def test_create_new_admin_over_existing_user(self, client, admin_user, regular_user):
        client.force_login(admin_user)
        url = reverse("admin_create")
        response = client.post(url,{
            "email": regular_user.email,
            "phone": regular_user.phone,
            "user_fio": regular_user.user_fio,
            "is_superuser": True,
        })
        assert response.status_code == 200
        user = get_user_model().objects.get(email=regular_user.email)
        assert user.is_staff == True

    def test_create_new_admin_regular_user(self, client, regular_user):
        client.force_login(regular_user)
        url = reverse("admin_create")
        response = client.post(url,{
            "email": "admin3@example.com",
            "phone": "+79110000004",
            "user_fio": "Test New Admin",
            "is_superuser": True,
        })

        assert response.status_code == 302
        assert response.url == reverse("admin_login")
        user = get_user_model().objects.filter(email="admin3@example.com").first()
        assert user is None