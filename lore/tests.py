from django.test import TestCase
from django.urls import reverse

from .forms import LoreEntryForm
from .models import LoreEntry


class LorePageTests(TestCase):
    def setUp(self):
        self.entry = LoreEntry.objects.create(
            entry_name="Eldrin",
            entry_description="An ancient figure in the setting.",
        )

    def test_lore_pages_render_and_redirects_use_valid_names(self):
        urls = [
            reverse("lore:list"),
            reverse("lore:create"),
            reverse("lore:detail", args=[self.entry.pk]),
            reverse("lore:edit", args=[self.entry.pk]),
            reverse("lore:delete", args=[self.entry.pk]),
        ]

        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_lore_names_are_unique_without_case_sensitivity(self):
        form = LoreEntryForm(
            data={
                "entry_name": "eldrin",
                "entry_type": "🧙‍♂️",
                "entry_description": "",
                "entry_author": "",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("A lore entry with this name already exists.", form.errors["entry_name"])
