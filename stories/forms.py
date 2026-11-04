from django import forms
from .models import Story, Scene, Choice
from core.forms import FormControlMixin


class StoryForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = Story
        fields = ['story_title', 'story_premise', 'story_genre', 'story_status', 'story_author']
        labels = {
            'story_title': 'Story Title',
            'story_premise': 'Story Premise',
            'story_genre': 'Story Genre',
            'story_status': 'Story Status',
            'story_author': 'Story Author',
        }
        help_texts = {
            'story_title': 'Enter the title of your story.',
            'story_premise': 'Provide a brief premise for your story (at least 20 characters).',
            'story_genre': 'Select the genre of your story.',
            'story_status': 'Select the current status of your story.',
            'story_author': 'Enter the author name (optional).',
        }
        widgets = {
            'story_title': forms.TextInput(attrs={'placeholder': 'Enter your story title'}),
            'story_premise': forms.Textarea(attrs={'placeholder': 'Summarize your story premise'}),
            'story_author': forms.TextInput(attrs={'placeholder': 'Enter the author name'}),
        }
        error_messages = {
            'story_title': {
                'required': 'Enter a title for your story.',
                'unique': "A story with this title already exists.",
            },
            'story_premise': {
                'required': 'Enter a premise for your story.',
                'min_length': "The premise must be at least 20 characters long.",
            },
        }


class StoryEditForm(StoryForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['story_author'].disabled = True


class SceneForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = Scene
        fields = ['story', 'scene_title', 'scene_content', 'scene_author', 'scene_start', 'scene_end', 'scene_order', 'lore_entries']
        labels = {
            'story': 'Story',
            'scene_title': 'Scene Title',
            'scene_content': 'Scene Content',
            'scene_author': 'Scene Author',
            'scene_start': 'Starting Scene',
            'scene_end': 'Ending Scene',
            'scene_order': 'Scene Order',
            'lore_entries': 'Lore Entries',
        }
        widgets = {
            'scene_title': forms.TextInput(attrs={'placeholder': 'Enter a scene title'}),
            'scene_content': forms.Textarea(attrs={'placeholder': 'Write the scene content'}),
            'scene_author': forms.TextInput(attrs={'placeholder': 'Enter the scene author'}),
        }
        help_texts = {
            'story': 'The story this scene belongs to.',
            'scene_title': 'Enter a title unique within this story.',
            'scene_content': 'Write the content of this scene.',
            'scene_author': 'Enter the author name (optional).',
            'scene_start': 'Mark this as the story starting scene.',
            'scene_end': 'Mark this as an ending scene.',
            'scene_order': 'Set the scene order within the story.',
            'lore_entries': 'Select lore entries associated with this scene.',
        }
        error_messages = {
            'scene_title': {
                'required': 'Enter a title for this scene.',
                'max_length': 'Scene titles can be at most 150 characters long.',
            },
            'scene_content': {'required': 'Enter the scene content.'},
            'scene_author': {
                'invalid': 'Use only letters, spaces, hyphens, and apostrophes in the author name.',
                'min_length': 'The author name must be at least 2 characters long.',
            },
            'scene_order': {
                'invalid': 'Enter a whole number for the scene order.',
                'min_value': 'The scene order cannot be negative.',
            },
        }

    def __init__(self, *args, **kwargs):
        story = kwargs.pop('story', None)
        super().__init__(*args, **kwargs)

        if story is None and self.instance.pk:
            story = self.instance.story

        self.fields['story'].disabled = True
        if story is not None:
            self.fields['story'].initial = story
            self.fields['story'].queryset = Story.objects.filter(pk=story.pk)

    def clean(self):
        cleaned_data = super().clean()
        story = cleaned_data.get('story')
        scene_start = cleaned_data.get('scene_start')
        scene_end = cleaned_data.get('scene_end')

        if scene_start and scene_end:
            self.add_error('scene_end', 'A scene cannot be both a start and an end scene.')

        if scene_end and self.instance.pk and self.instance.choices.exists():
            self.add_error(
                'scene_end',
                "Scenes with outgoing choices can't be marked as ending scenes.",
            )

        if story and scene_start:
            starting_scenes = Scene.objects.filter(story=story, scene_start=True)
            if self.instance.pk:
                starting_scenes = starting_scenes.exclude(pk=self.instance.pk)
            if starting_scenes.exists():
                self.add_error(
                    'scene_start',
                    'There can only be one start scene per story.',
                )

        return cleaned_data


class ChoiceForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['text', 'current_scene', 'next_scene']
        labels = {
            'text': 'Choice Text',
            'current_scene': 'Current Scene',
            'next_scene': 'Next Scene',
        }
        widgets = {
            'text': forms.TextInput(attrs={'placeholder': 'Enter the choice text'}),
        }
        help_texts = {
            'text': 'Describe the option the reader can choose.',
            'current_scene': 'The scene this choice leaves from.',
            'next_scene': 'Choose the destination scene, or leave blank for no destination.',
        }
        error_messages = {
            'text': {
                'required': 'Enter text for this choice.',
                'max_length': 'Choice text can be at most 200 characters long.',
            },
            'current_scene': {'required': 'A current scene is required.'},
        }

    def __init__(self, *args, **kwargs):
        story = kwargs.pop('story', None)
        scene = kwargs.pop('scene', None)
        super().__init__(*args, **kwargs)

        if story is None and scene is not None:
            story = scene.story
        if story is None and self.instance.pk and self.instance.current_scene_id:
            story = self.instance.current_scene.story

        scenes = Scene.objects.filter(story=story) if story is not None else Scene.objects.none()
        self.fields['current_scene'].queryset = scenes
        self.fields['current_scene'].disabled = True
        if scene is not None:
            self.fields['current_scene'].initial = scene
        self.fields['next_scene'].queryset = scenes

    def clean(self):
        cleaned_data = super().clean()
        current_scene = cleaned_data.get('current_scene')
        next_scene = cleaned_data.get('next_scene')

        if current_scene and next_scene and current_scene.story != next_scene.story:
            self.add_error(
                'next_scene',
                'The selected scenes must belong to the same story.',
            )

        if current_scene and next_scene and current_scene == next_scene:
            self.add_error(
                'next_scene',
                'The next scene cannot be the same as the current scene.',
            )

        return cleaned_data


class StoryFilterForm(FormControlMixin, forms.Form):
    story_title = forms.CharField(
        required=False,
        label='Title',
        help_text='Filter stories by title.',
        widget=forms.TextInput(attrs={'placeholder': 'Story Title'}),
    )
    story_genre = forms.ChoiceField(
        required=False,
        label='Genre',
        help_text='Filter stories by genre.',
        choices=[('', 'All Genres')] + list(Story.GENRES),
        widget=forms.Select(),
    )
    story_status = forms.ChoiceField(
        required=False,
        label='Status',
        help_text='Filter stories by status.',
        choices=[('', 'All Statuses')] + list(Story.STATUS),
        widget=forms.Select(),
    )
    story_author = forms.CharField(
        required=False,
        label='Author',
        help_text='Filter stories by author.',
        widget=forms.TextInput(attrs={'placeholder': 'Author Name'}),
    )
    sort_by = forms.ChoiceField(
        required=False,
        label='Sort by',
        help_text='Choose how matching stories are ordered.',
        choices=[
            ('', 'Default order'),
            ('title', 'Title'),
            ('newest', 'Newest'),
            ('oldest', 'Oldest'),
        ],
        widget=forms.Select(),
    )