from django.contrib.auth import get_user_model

import pytest

User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        email="admin@example.com",
        password="password123",
        phone="+79110000000",
        user_fio="Test Testovich Testov",
        is_staff=True,
    )


@pytest.fixture
def admin_user2(db):
    return User.objects.create_user(
        email="admin2@example.com",
        password="password123",
        phone="+79110000001",
        user_fio="Test Testovich Testov Second",
        is_staff=True,
    )


@pytest.fixture
def regular_user(db):
    return User.objects.create_user(
        email="user@example.com",
        user_fio="Regular Gay",
        password="password123",
        phone="71000000000"
    )
