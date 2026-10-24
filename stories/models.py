from django.core.exceptions import ValidationError
from django.core.validators import MinLengthValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse

from core.models import TimeStampedModel
from .validators import validate_author_name, min_author_name_length, non_whitespace_validator

class Story(TimeStampedModel):
    GENRES = [
        ('❤️', 'Romance'),
        ('🕵️', 'Mystery'),
        ('⚔️', 'Fantasy'),
        ('👽', 'Sci-Fi'),
        ('👻', 'Horror'),
        ('📜', 'Historical'),
        ('🧒', 'Young Adult'),
        ('?', 'Other/No genre'),
    ]

    STATUS = [
        ('📝', 'Draft'),
        ('✍', 'Open'),
        ('✅', 'Complete')
    ]

    story_title = models.CharField(max_length=150, unique=True)
    story_premise = models.TextField(validators=[MinLengthValidator(20), non_whitespace_validator])
    story_genre = models.CharField(max_length=20, choices=GENRES, default='?')
    story_status = models.CharField(max_length=20, choices=STATUS, default='📝')
    story_author = models.CharField(max_length=100, blank=True, validators=[validate_author_name, min_author_name_length])

    def __str__(self):
        return self.story_title

    @property
    def is_open(self):
        return self.story_status == '✍'
    def get_start_scene(self):
        return self.scenes.filter(scene_start=True).first()

class Scene(TimeStampedModel):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='scenes')
    scene_title = models.CharField(max_length=150)
    scene_content = models.TextField()
    scene_author = models.CharField(max_length=100, blank=True, validators=[validate_author_name, min_author_name_length])
    scene_start = models.BooleanField(default=False)
    scene_end = models.BooleanField(default=False)
    scene_order = models.PositiveIntegerField(default=0)

    lore_entries = models.ManyToManyField('lore.LoreEntry', blank=True, related_name='scenes')

    class Meta:
        ordering = ['scene_order']
        verbose_name = "Scene"
        verbose_name_plural = "Scenes"
        constraints = [
            models.UniqueConstraint(fields=['story', 'scene_title'], name='unique_scene_title_per_story', violation_error_message="A scene with this title already exists for this story."),
            models.UniqueConstraint(fields=['story'], condition=models.Q(scene_start=True), name='unique_start_scene_per_story', violation_error_message="There can only be one start scene per story."),
            models.CheckConstraint(condition=~Q(scene_start=True, scene_end=True), name='scene_cant_be_both', violation_error_message="A scene cannot be both a start and an end scene."),
        ]

    def __str__(self):
        return f"{self.scene_title} — {self.story.story_title}"

    @property
    def is_dead_end(self):
        return not self.scene_end and not self.choices.exists()

    def get_absolute_url(self):
        return reverse('stories:scene_detail', kwargs={'pk': self.pk})

class Choice(models.Model):
    text = models.CharField(max_length=200)
    current_scene = models.ForeignKey(Scene, on_delete=models.CASCADE, related_name='choices')
    next_scene = models.ForeignKey(Scene, on_delete=models.SET_NULL, null=True, blank=True, related_name='incoming_choices')

    class Meta:
        ordering = ['id']
        verbose_name = "Choice"
        verbose_name_plural = "Choices"
        constraints = [
            models.UniqueConstraint(fields=['current_scene', 'text'], name='unique_choice_text_per_scene', violation_error_message="A choice with this text already exists for this scene.")
        ]

    def clean(self):
        super().clean()

        if self.current_scene.story and self.next_scene and self.current_scene.story != self.next_scene.story:
            raise ValidationError("The next scene must belong to the same story as the current scene.")
    
    def __str__(self):
        return f"Choice: {self.text} (from Scene: {self.current_scene.scene_title})"