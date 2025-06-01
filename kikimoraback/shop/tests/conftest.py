from django.contrib.auth import get_user_model

import pytest
from model_bakery import baker

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
def products_set_1(subcategories):
    products = baker.make(
        "Product",
        _quantity=10,
        price=10.0,
        weight=1.5,
        description="Default description",
        name=baker.seq("Product", start=1),
    )
    for product in products:
        product.subcategory.add(subcategories[0])  # добавляем связь после сохранения
    return products


@pytest.fixture
def products_set_2(subcategories):
    products = baker.make(
        "Product",
        price=10.0,
        weight=1.5,
        description="Default description",
        _quantity=10,
        name=baker.seq("Product2", start=1),
    )
    for product in products:
        product.subcategory.add(subcategories[1])
    return products


@pytest.fixture
def tags(products_set_1, products_set_2):
    tags_list = baker.make("ProductTag", text=baker.seq("Tag", start=1), _quantity=3)
    for product in products_set_2:
        product.tag = tags_list[0]
        product.save()

    for product in products_set_1:
        product.tag = tags_list[1]
        product.save()

    return tags_list


@pytest.fixture
def discounts_category_fixture():
    return baker.make_recipe("shop.discount_category_recipe")


@pytest.fixture
def discount_subcategory_recipe():
    return baker.make_recipe("shop.discount_subcategory_recipe")


@pytest.fixture
def discounts_product_fixture():
    return baker.make_recipe("shop.discount_product_recipe")


@pytest.fixture
def promo_fixtures():
    return baker.make_recipe("shop.promocode_recipe", _quantity=5)


@pytest.fixture
def limit_time_fixture():
    return baker.make_recipe("shop.limite_time_recipe", _quantity=5)
