from django.urls import reverse
from shop.models import Subcategory
import pytest

@pytest.mark.django_db
class TestSubcategoryListView:
    def test_get_subcategory_page(self, client, admin_user, subcategories, category):
        client.force_login(admin_user)
        url = reverse('subcategory_list', kwargs={'category_id': category.category_id})
        response = client.get(url)

        assert response.status_code == 200
        assert len(response.context['subcategories']) == len(Subcategory.objects.all())