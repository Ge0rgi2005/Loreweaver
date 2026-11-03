from django.test import TestCase
from django.urls import reverse

from .forms import ChoiceForm, SceneForm, StoryEditForm
from .models import Choice, Scene, Story
from .services import check_story_health


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


class StoryHealthTests(TestCase):
    def setUp(self):
        self.story = Story.objects.create(
            story_title="Health Test Tale",
            story_premise="A sufficiently long premise for this health test.",
        )

    def make_scene(self, title, **flags):
        return Scene.objects.create(
            story=self.story,
            scene_title=title,
            scene_content=f"{title} content.",
            **flags,
        )

    def test_health_report_handles_a_loop_and_reachable_ending_in_two_queries(self):
        start = self.make_scene("Start", scene_start=True)
        loop = self.make_scene("Loop")
        ending = self.make_scene("Ending", scene_end=True)
        Choice.objects.create(text="Enter loop", current_scene=start, next_scene=loop)
        Choice.objects.create(text="Go back", current_scene=loop, next_scene=start)
        Choice.objects.create(text="Finish", current_scene=loop, next_scene=ending)

        with self.assertNumQueries(3):
            report = check_story_health(self.story)

        self.assertTrue(report.has_start)
        self.assertEqual(report.unreachable, [])
        self.assertEqual(report.dead_ends, [])
        self.assertEqual(report.reachable_endings, [ending])
        self.assertTrue(report.is_healthy)

    def test_health_report_finds_an_orphan_scene(self):
        start = self.make_scene("Start", scene_start=True)
        ending = self.make_scene("Ending", scene_end=True)
        orphan = self.make_scene("Orphan")
        Choice.objects.create(text="Finish", current_scene=start, next_scene=ending)

        report = check_story_health(self.story)

        self.assertEqual(report.unreachable, [orphan])
        self.assertEqual(report.dead_ends, [orphan])
        self.assertFalse(report.is_healthy)

    def test_health_report_finds_choices_without_a_destination(self):
        start = self.make_scene("Start", scene_start=True)
        open_choice = Choice.objects.create(
            text="Choose later",
            current_scene=start,
        )

        report = check_story_health(self.story)

        self.assertEqual(report.open_choices, [open_choice])
        self.assertEqual(report.dead_ends, [])
        self.assertFalse(report.is_healthy)

    def test_health_report_finds_no_reachable_endings(self):
        start = self.make_scene("Start", scene_start=True)
        next_scene = self.make_scene("Next")
        Choice.objects.create(text="Continue", current_scene=start, next_scene=next_scene)

        report = check_story_health(self.story)

        self.assertEqual(report.reachable_endings, [])
        self.assertFalse(report.is_healthy)

    def test_health_report_handles_an_empty_story(self):
        report = check_story_health(self.story)

        self.assertFalse(report.has_start)
        self.assertEqual(report.dead_ends, [])
        self.assertEqual(report.open_choices, [])
        self.assertEqual(report.unreachable, [])
        self.assertEqual(report.reachable_endings, [])
        self.assertFalse(report.is_healthy)

    def test_health_page_renders_report(self):
        self.make_scene("Opening", scene_start=True)

        response = self.client.get(reverse("stories:health", args=[self.story.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["story"], self.story)
        self.assertFalse(response.context["report"].is_healthy)


class StoryPlayTests(TestCase):
    def setUp(self):
        self.story = Story.objects.create(
            story_title="Play Test Tale",
            story_premise="A sufficiently long premise for this play test.",
        )
        self.start = Scene.objects.create(
            story=self.story,
            scene_title="Opening",
            scene_content="The story begins.",
            scene_start=True,
        )
        self.ending = Scene.objects.create(
            story=self.story,
            scene_title="The End",
            scene_content="The story is over.",
            scene_end=True,
        )
        self.choice = Choice.objects.create(
            text="Finish the story",
            current_scene=self.start,
            next_scene=self.ending,
        )

    def test_reader_can_follow_choice_to_ending_and_restart(self):
        play_url = reverse("stories:play", args=[self.story.pk])
        response = self.client.get(play_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["scene"], self.start)
        self.assertEqual(response.context["steps"], 0)

        response = self.client.post(
            reverse(
                "stories:play_choose",
                args=[self.story.pk, self.choice.pk],
            )
        )
        self.assertRedirects(response, play_url)

        response = self.client.get(play_url)
        self.assertEqual(response.context["scene"], self.ending)
        self.assertTrue(response.context["finished"])
        self.assertEqual(response.context["steps"], 1)
        self.assertEqual(response.context["path"], [self.start, self.ending])
        self.assertContains(response, "The End")

        response = self.client.post(
            reverse("stories:play_restart", args=[self.story.pk])
        )
        self.assertRedirects(response, play_url)
        response = self.client.get(play_url)
        self.assertEqual(response.context["scene"], self.start)
        self.assertEqual(response.context["steps"], 0)

    def test_choice_cannot_be_used_from_another_scene(self):
        unrelated = Scene.objects.create(
            story=self.story,
            scene_title="Other",
            scene_content="Other.",
        )
        invalid_choice = Choice.objects.create(
            text="Skip ahead",
            current_scene=unrelated,
            next_scene=self.ending,
        )

        self.client.get(reverse("stories:play", args=[self.story.pk]))
        response = self.client.post(
            reverse(
                "stories:play_choose",
                args=[self.story.pk, invalid_choice.pk],
            )
        )

        self.assertRedirects(response, reverse("stories:play", args=[self.story.pk]))
        self.assertEqual(
            self.client.get(reverse("stories:play", args=[self.story.pk])).context["scene"],
            self.start,
        )

    def test_invalid_session_scene_is_reset_to_start(self):
        session = self.client.session
        session[f"play_{self.story.pk}"] = [999999]
        session.save()

        response = self.client.get(reverse("stories:play", args=[self.story.pk]))

        self.assertEqual(response.context["scene"], self.start)
        self.assertEqual(response.context["path"], [self.start])

    def test_story_without_start_redirects_with_message(self):
        self.start.scene_start = False
        self.start.save()

        response = self.client.get(reverse("stories:play", args=[self.story.pk]))

        self.assertRedirects(response, reverse("stories:detail", args=[self.story.pk]))
