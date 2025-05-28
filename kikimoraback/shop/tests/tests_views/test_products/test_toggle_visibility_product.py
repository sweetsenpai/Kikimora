import pytest
from shop.models import Product
from django.urls import reverse

@pytest.mark.django_db
class TestToogleVisabilityProduct:
    def test_valid_togle(self,client, admin_user, products_set_1):
        client.force_login(admin_user)

        product_before = products_set_1[0]
        url = reverse('change_visibility_product', kwargs={'product_id': product_before.product_id})
        response = client.post(url)

        product_affter = Product.objects.get(prodcut_id=product_before.product_id,)

        assert response.status_code == 200
        assert product_before.visability != product_affter.visability

    def test_toggle_non_existing_product(self, client, admin_user):
        client.force_login(admin_user)

        url = reverse('change_visibility_product', kwargs={'product_id': 6000})
        response = client.post(url)
        assert response.status_code == 404

    def test_not_admin_togle(self,client, regular_user, products_set_1):
        client.force_login(regular_user)
        product_before = products_set_1[0]
        url = reverse('change_visibility_product', kwargs={'product_id': product_before.product_id})
        response = client.post(url)

        product_affter = Product.objects.get(product_id=product_before.product_id)

        assert response.status_code == 302
        assert product_before.visability == product_affter.visability

    def test_toogle_get(self, client, admin_user, products_set_1):
        client.force_login(admin_user)

        product_before = products_set_1[0]
        url = reverse('change_visibility_product', kwargs={'product_id': product_before.product_id})
        response = client.get(url)

        product_affter = Product.obkects.get(product_id=product_before.product_id)

        assert response.status_code == 400
        assert product_before.visability == product_affter.visability