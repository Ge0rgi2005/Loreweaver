from dataclasses import dataclass

from django.db.models import Count

from .models import Choice, Scene, Story


@dataclass
class StoryHealthReport:
    has_start: bool
    dead_ends: list[Scene]
    open_choices: list[Choice]
    unreachable: list[Scene]
    reachable_endings: list[Scene]

    @property
    def is_healthy(self):
        return (
            self.has_start
            and not self.dead_ends
            and not self.open_choices
            and not self.unreachable
            and bool(self.reachable_endings)
        )


def check_story_health(story: Story) -> StoryHealthReport:
    scenes = list(
        Scene.objects.filter(story=story).annotate(choice_count=Count("choices"))
    )
    edges = Choice.objects.filter(current_scene__story=story).values_list(
        "current_scene_id", "next_scene_id"
    )
    open_choices = list(
        Choice.objects.filter(
            current_scene__story=story, next_scene__isnull=True
        ).select_related("current_scene")
    )
    scenes_by_id = {scene.pk: scene for scene in scenes}
    start_scene = next((scene for scene in scenes if scene.scene_start), None)

    graph = {scene.pk: [] for scene in scenes}
    for origin_id, destination_id in edges:
        if destination_id in scenes_by_id:
            graph[origin_id].append(destination_id)

    reachable = set()
    if start_scene:
        pending = [start_scene.pk]
        while pending:
            scene_id = pending.pop()
            if scene_id in reachable:
                continue
            reachable.add(scene_id)
            pending.extend(graph[scene_id])

    return StoryHealthReport(
        has_start=start_scene is not None,
        dead_ends=[
            scene
            for scene in scenes
            if not scene.scene_end and scene.choice_count == 0
        ],
        open_choices=open_choices,
        unreachable=[
            scene for scene in scenes if scene.pk not in reachable
        ],
        reachable_endings=[
            scene
            for scene in scenes
            if scene.pk in reachable and scene.scene_end
        ],
    )
