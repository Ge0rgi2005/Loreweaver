from django import forms
from django.core.exceptions import ValidationError
from .models import Story, Scene, Choice


class StoryForm(forms.ModelForm):
    class Meta:
        model = Story
        fields = ['story_title', 'story_premise', 'story_genre', 'story_status', 'story_author']
        labels = {'story_title': 'Title','story_premise': 'Premise','story_genre': 'Genre','story_status': 'Status', 'story_author': 'Author',}
        help_texts = {
            'story_title': 'Enter the title of your story.',
            'story_premise': 'Provide a brief premise for your story (at least 20 characters).',
            'story_genre': 'Select the genre of your story.',
            'story_status': 'Select the current status of your story.',
            'story_author': 'Enter the author name (optional).',
        }
        widgets = {
            'story_title': forms.TextInput(attrs={'class': 'form-control'}),
            'story_premise': forms.Textarea(attrs={'class': 'form-control'}),
            'story_genre': forms.Select(attrs={'class': 'form-control'}),
            'story_status': forms.Select(attrs={'class': 'form-control'}),
            'story_author': forms.TextInput(attrs={'class': 'form-control'}),
        }
        error_messages = {
            'story_title': {
                'unique': "A story with this title already exists.",
            },
            'story_premise': {
                'min_length': "The premise must be at least 20 characters long.",
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['story_title'].label = 'Story Title'
        self.fields['story_premise'].label = 'Story Premise'
        self.fields['story_genre'].label = 'Story Genre'
        self.fields['story_status'].label = 'Story Status'
        self.fields['story_author'].label = 'Story Author'


class SceneForm(forms.ModelForm):
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
            'story': forms.Select(attrs={'class': 'form-control'}),
            'scene_title': forms.TextInput(attrs={'class': 'form-control'}),
            'scene_content': forms.Textarea(attrs={'class': 'form-control'}),
            'scene_author': forms.TextInput(attrs={'class': 'form-control'}),
            'scene_start': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'scene_end': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'scene_order': forms.NumberInput(attrs={'class': 'form-control'}),
            'lore_entries': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'lore_entries': 'Select lore entries associated with this scene.',
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


class ChoiceForm(forms.ModelForm):
    class Meta:
        model = Choice
        fields = ['text', 'current_scene', 'next_scene']
        labels = {'text': 'Text','current_scene': 'Current Scene', 'next_scene': 'Next Scene',}
        widgets = {
            'text': forms.TextInput(attrs={'class': 'form-control'}),
            'current_scene': forms.Select(attrs={'class': 'form-control'}),
            'next_scene': forms.Select(attrs={'class': 'form-control'}),
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
        self.fields['next_scene'].queryset = scenes

    def clean(self):
        cleaned_data = super().clean()
        current_scene = cleaned_data.get('current_scene')
        next_scene = cleaned_data.get('next_scene')

        if current_scene and next_scene and current_scene.story != next_scene.story:
            raise ValidationError('The selected scenes must belong to the same story.')

        if current_scene and next_scene and current_scene == next_scene:
            raise ValidationError('The next scene cannot be the same as the current scene.')

        return cleaned_data


class StoryFilterForm(forms.Form):
    story_title = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Story Title'}),)
    story_genre = forms.ChoiceField(required=False, choices=[('', 'All Genres')] + list(Story.GENRES), widget=forms.Select(attrs={'class': 'form-control'}),)
    story_status = forms.ChoiceField(required=False, choices=[('', 'All Statuses')] + list(Story.STATUS), widget=forms.Select(attrs={'class': 'form-control'}),)
    story_author = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Author Name'}),)