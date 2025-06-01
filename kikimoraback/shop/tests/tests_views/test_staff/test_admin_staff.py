from django.urls import reverse

import pytest


@pytest.mark.django_db
class TestAdminStaff:
    def test_get_all_staff(self, client, admin_user, admin_user2, regular_user):
        client.force_login(admin_user)
        url = reverse("staff")
        response = client.get(url)

        assert response.status_code == 200

        # Получаем список пользователей из контекста
        admins = response.context["admins"]

        # Приводим QuerySet к множеству ID для сравнения
        admin_ids = set(user.user_id for user in admins)
        expected_ids = {admin_user.user_id, admin_user2.user_id}

        # Проверяем, что только админы попали в результат
        assert admin_ids == expected_ids
        assert regular_user.user_id not in admin_ids

    def test_post_search_by_email(self, client, admin_user, admin_user2):
        client.force_login(admin_user)
        url = reverse("staff")

        # Передаём email второго админа в query params
        response = client.get(url, {"email": admin_user2.email})

        assert response.status_code == 200

        admins = response.context["admins"]

        # Должен быть только один пользователь в результатах — admin_user2
        assert len(admins) == 1
        assert admins[0].email == admin_user2.email

    def test_access_denied_for_non_staff(self, client, regular_user):
        client.force_login(regular_user)
        url = reverse("staff")
        response = client.get(url)
        assert response.url == reverse("admin_login")
