from django.test import SimpleTestCase
from django.urls import reverse


class HomepageTests(SimpleTestCase):
    def test_url_exists_at_correct_location(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)

    def test_homepage_url_name(self):
        response = self.client.get(reverse("admin_home"))
        self.assertEqual(response.status_code, 200)

    def test_homepage_template(self):  # new
        response = self.client.get("/")
        self.assertTemplateUsed(response, "master/home.html")
