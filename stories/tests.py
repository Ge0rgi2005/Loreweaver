from django.test import TestCase
from django.urls import reverse

from .forms import ChoiceForm, SceneForm, StoryEditForm
from .models import Choice, Scene, Story


class StoryPageTests(TestCase):
    def setUp(self):
        self.story = Story.objects.create(
            story_title="The First Tale",
            story_premise="A sufficiently long premise for this story.",
            story_status="✍",
        )
        self.scene = Scene.objects.create(
            story=self.story,
            scene_title="Opening",
            scene_content="The story begins here.",
        )

    def test_story_and_scene_pages_render(self):
        urls = [
            reverse("core:home"),
            reverse("stories:list"),
            reverse("stories:create"),
            reverse("stories:detail", args=[self.story.pk]),
            reverse("stories:edit", args=[self.story.pk]),
            reverse("stories:delete", args=[self.story.pk]),
            reverse("scenes:detail", args=[self.scene.pk]),
            reverse("scenes:edit", args=[self.scene.pk]),
            reverse("scenes:delete", args=[self.scene.pk]),
            reverse("stories:scene_create", args=[self.story.pk]),
            reverse("scenes:choice_create", args=[self.scene.pk]),
        ]

        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_story_list_filters_title_and_annotates_scene_count(self):
        response = self.client.get(reverse("stories:list"), {"story_title": "First"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["stories"]), [self.story])
        self.assertEqual(response.context["stories"][0].scene_count, 1)
        self.assertContains(response, 'name="sort_by"')

    def test_story_list_supports_requested_sort_order(self):
        earlier_story = Story.objects.create(
            story_title="A Earlier Tale",
            story_premise="A sufficiently long premise for an earlier tale.",
        )

        response = self.client.get(
            reverse("stories:list"),
            {"sort_by": "newest"},
        )

        self.assertEqual(
            list(response.context["stories"]),
            [earlier_story, self.story],
        )

    def test_story_create_redirects_to_detail(self):
        response = self.client.post(
            reverse("stories:create"),
            {
                "story_title": "Another Tale",
                "story_premise": "Another sufficiently long story premise.",
                "story_genre": "?",
                "story_status": "📝",
                "story_author": "",
            },
        )

        story = Story.objects.get(story_title="Another Tale")
        self.assertRedirects(response, story.get_absolute_url())

    def test_scene_creation_only_allows_open_stories(self):
        closed_story = Story.objects.create(
            story_title="A Closed Tale",
            story_premise="A sufficiently long premise for this closed story.",
        )

        response = self.client.get(
            reverse("stories:scene_create", args=[closed_story.pk])
        )

        self.assertRedirects(response, reverse("stories:detail", args=[closed_story.pk]))

    def test_choice_form_has_scene_choices_and_invalid_post_is_safe(self):
        response = self.client.get(reverse("scenes:choice_create", args=[self.scene.pk]))

        self.assertContains(response, f'value="{self.scene.pk}"')
        self.assertTrue(response.context["form"].fields["current_scene"].disabled)

        invalid_response = self.client.post(
            reverse("scenes:choice_create", args=[self.scene.pk]),
            {},
        )
        self.assertEqual(invalid_response.status_code, 200)
        self.assertFalse(Choice.objects.exists())

    def test_choice_errors_are_attached_to_the_relevant_fields(self):
        ending_scene = Scene.objects.create(
            story=self.story,
            scene_title="Ending",
            scene_content="The story ends here.",
            scene_end=True,
        )
        ending_form = ChoiceForm(
            data={"text": "Continue", "next_scene": ""},
            scene=ending_scene,
        )

        self.assertFalse(ending_form.is_valid())
        self.assertIn("Ending scenes can't have outgoing choices.", ending_form.errors["current_scene"])
        self.assertNotIn("__all__", ending_form.errors)

        same_scene_form = ChoiceForm(
            data={"text": "Stay", "next_scene": self.scene.pk},
            scene=self.scene,
        )
        self.assertFalse(same_scene_form.is_valid())
        self.assertIn(
            "The next scene cannot be the same as the current scene.",
            same_scene_form.errors["next_scene"],
        )

    def test_scene_constraints_are_attached_to_fields_and_exclude_the_instance(self):
        start_scene = self.scene
        start_scene.scene_start = True
        start_scene.save()

        duplicate_start_form = SceneForm(
            data={
                "scene_title": "Another opening",
                "scene_content": "This cannot also be the start.",
                "scene_author": "",
                "scene_start": "on",
                "scene_order": "1",
                "lore_entries": [],
            },
            story=self.story,
        )
        self.assertFalse(duplicate_start_form.is_valid())
        self.assertIn(
            "There can only be one start scene per story.",
            duplicate_start_form.errors["scene_start"],
        )
        self.assertNotIn("__all__", duplicate_start_form.errors)

        both_flags_form = SceneForm(
            data={
                "scene_title": "Conflicting flags",
                "scene_content": "This cannot start and end.",
                "scene_author": "",
                "scene_start": "on",
                "scene_end": "on",
                "scene_order": "2",
                "lore_entries": [],
            },
            story=Story.objects.create(
                story_title="Another Story",
                story_premise="A sufficiently long premise for another story.",
            ),
        )
        self.assertFalse(both_flags_form.is_valid())
        self.assertIn(
            "A scene cannot be both a start and an end scene.",
            both_flags_form.errors["scene_end"],
        )
        self.assertNotIn("__all__", both_flags_form.errors)

        edit_form = SceneForm(
            data={
                "scene_title": start_scene.scene_title,
                "scene_content": start_scene.scene_content,
                "scene_author": "",
                "scene_start": "on",
                "scene_order": "0",
                "lore_entries": [],
            },
            instance=start_scene,
            story=self.story,
        )
        self.assertTrue(edit_form.is_valid(), edit_form.errors)

    def test_forms_use_shared_widget_classes_and_story_author_is_disabled_on_edit(self):
        story_form = StoryEditForm(instance=self.story)
        scene_form = SceneForm(story=self.story)
        choice_form = ChoiceForm(scene=self.scene)

        self.assertEqual(
            story_form.fields["story_title"].widget.attrs["class"],
            "form-control",
        )
        self.assertEqual(
            scene_form.fields["story"].widget.attrs["class"],
            "form-select",
        )
        self.assertEqual(
            scene_form.fields["scene_start"].widget.attrs["class"],
            "form-check-input",
        )
        self.assertEqual(
            choice_form.fields["next_scene"].widget.attrs["class"],
            "form-select",
        )
        self.assertTrue(story_form.fields["story_author"].disabled)

    def test_choice_create_and_delete_routes_work(self):
        response = self.client.post(
            reverse("scenes:choice_create", args=[self.scene.pk]),
            {
                "text": "Continue",
                "current_scene": self.scene.pk,
                "next_scene": "",
            },
        )
        choice = Choice.objects.get(text="Continue")
        self.assertRedirects(
            response, reverse("scenes:detail", args=[self.scene.pk])
        )

        delete_url = reverse("choices:delete", args=[choice.pk])
        self.assertEqual(self.client.get(delete_url).status_code, 200)
        self.assertRedirects(
            self.client.post(delete_url),
            reverse("scenes:detail", args=[self.scene.pk]),
        )

    def test_story_filter_rejects_unknown_sort_without_skipping_other_filters(self):
        response = self.client.get(
            reverse("stories:list"),
            {"story_title": "First", "sort_by": "not-allowed"},
        )

        self.assertEqual(list(response.context["stories"]), [self.story])
        self.assertContains(response, 'name="sort_by"')

    def test_story_delete_redirects_and_removes_story(self):
        response = self.client.post(reverse("stories:delete", args=[self.story.pk]))

        self.assertRedirects(response, reverse("stories:list"))
        self.assertFalse(Story.objects.filter(pk=self.story.pk).exists())
