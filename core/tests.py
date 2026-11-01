from django.test import TestCase
from django.urls import reverse


class CorePageTests(TestCase):
    def test_home_and_about_pages_render(self):
        self.assertEqual(self.client.get(reverse("core:home")).status_code, 200)
        self.assertEqual(self.client.get(reverse("core:about")).status_code, 200)
