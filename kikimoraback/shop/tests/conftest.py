from django.contrib.auth import get_user_model

import pytest
from model_bakery import baker

from shop.models import *

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
        phone="71000000000",
    )


@pytest.fixture
def category(db):
    return baker.make("Category", name="Test Category")


@pytest.fixture
def subcategories(category):
    return baker.make("SubCategory", category=category, _quantity=2)


@pytest.fixture
def products(subcategories):
    products = []
    for subcat in subcategories:
        products += baker.make(
            "Product",
            subcategory=subcat,
            _quantity=10,
            name=baker.seq("Product {}", start=1),
        )
    return products
