from django.test import TestCase
from django.urls import reverse


class CorePageTests(TestCase):
    def test_home_and_about_pages_render(self):
        self.assertEqual(self.client.get(reverse("core:home")).status_code, 200)
        about_response = self.client.get(reverse("core:about"))
        self.assertEqual(about_response.status_code, 200)
        self.assertContains(about_response, "Weave a world together")
        self.assertContains(about_response, reverse("lore:list"))
