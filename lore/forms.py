from django import forms
from .models import LoreEntry
from core.forms import FormControlMixin


class LoreEntryForm(FormControlMixin, forms.ModelForm):
    class Meta:
        model = LoreEntry
        fields = ['entry_name', 'entry_type', 'entry_description', 'entry_author']
        labels = {
            'entry_name': 'Entry Name',
            'entry_type': 'Entry Type',
            'entry_description': 'Entry Description',
            'entry_author': 'Entry Author',
        }
        widgets = {
            'entry_name': forms.TextInput(attrs={'placeholder': 'Enter the lore entry name'}),
            'entry_description': forms.Textarea(attrs={'placeholder': 'Describe this lore entry'}),
            'entry_author': forms.TextInput(attrs={'placeholder': 'Enter the author name'}),
        }
        help_texts = {
            'entry_name': 'Enter the name of the lore entry.',
            'entry_type': 'Select the type of the lore entry.',
            'entry_description': 'Provide a description for the lore entry.',
            'entry_author': 'Enter the author name (optional).',
        }
        error_messages = {
            'entry_name': {
                'required': 'Enter a name for this lore entry.',
                'max_length': 'Lore entry names can be at most 100 characters long.',
            },
            'entry_author': {
                'invalid': 'Use only letters, spaces, hyphens, and apostrophes in the author name.',
                'min_length': 'The author name must be at least 2 characters long.',
            },
        }

    def clean_entry_name(self):
        entry_name = self.cleaned_data.get('entry_name')
        if not entry_name:
            return entry_name

        duplicates = LoreEntry.objects.filter(entry_name__iexact=entry_name)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("A lore entry with this name already exists.")
        return entry_name