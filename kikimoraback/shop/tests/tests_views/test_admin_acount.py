from django.urls import reverse
from django.contrib.auth import get_user_model
import pytest


class TestAdminAccount:
    def test_admin_acount_get_existing_admin(self, client, admin_user, admin_user2):
        client.force_login(admin_user)
        url = reverse('admin_account', kwargs={'admin_id': admin_user2.user_id})
        response = client.get(url)

        assert response.status_code == 200
        assert response.context['admin'].user_fio == admin_user2.user_fio

    def test_admin_acount_get_non_existing_admin(self, client, admin_user):
        client.force_login(admin_user)
        url = reverse('admin_account', kwargs={'admin_id': 8000})
        response = client.get(url)

        assert response.status_code == 404

    def test_delete_admin_acount(self, client, admin_user, admin_user2):
        client.force_login(admin_user)
        url = reverse('admin_account', kwargs={'admin_id': admin_user2.user_id})
        response = client.post(url)

        assert response.status_code == 200
        user = get_user_model().objects.get(email = admin_user2.email)
        assert user is not None
        assert user.is_staff == False

    def test_admin_acount_get_by_not_admin(self, client, regular_user):
        client.force_login(regular_user)
        url = reverse('admin_account', kwargs={'admin_id': 1})
        response = client.get(url)

        assert response.status_code == 302
        assert response.url.startswith("/accounts/login")