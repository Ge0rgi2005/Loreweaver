from django.db import models

from core.models import TimeStampedModel
from .validators import validate_author_name, min_author_name_length, non_whitespace_validator

class LoreEntry(TimeStampedModel):
    CHOICES = [
    ('🧙‍♂️', 'Character'),
    ('🏰', 'Location'),
    ('📜', 'Artifact'),
    ('🧩', 'Event'),
    ('👥', 'Faction'),
]
    
    entry_name = models.CharField(max_length=100)
    entry_type = models.CharField(max_length=20, choices=CHOICES, default='🧙‍♂️')
    entry_description = models.TextField(blank=True, validators=[non_whitespace_validator])
    entry_author = models.CharField(max_length=100, blank=True, validators=[validate_author_name, min_author_name_length])

    class Meta:
        ordering = ['entry_name']
        verbose_name = "Lore Entry"
        verbose_name_plural = "Lore Entries"
        constraints = [
            models.UniqueConstraint(fields=['entry_name'], name='unique_entry_name', violation_error_message="A lore entry with this name already exists."),
        ]

    def __str__(self):
        return f"{self.entry_name} ({self.get_entry_type_display()})"