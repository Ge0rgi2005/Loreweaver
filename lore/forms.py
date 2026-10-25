from django import forms
from .models import LoreEntry

class LoreEntryForm(forms.ModelForm):
    class Meta:
        model = LoreEntry
        fields = ['entry_name', 'entry_type', 'entry_description', 'entry_author']
        widgets = {
            'entry_name': forms.TextInput(attrs={'class': 'form-control'}),
            'entry_type': forms.Select(attrs={'class': 'form-control'}),
            'entry_description': forms.Textarea(attrs={'class': 'form-control'}),
            'entry_author': forms.TextInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'entry_name': 'Enter the name of the lore entry.',
            'entry_type': 'Select the type of the lore entry.',
            'entry_description': 'Provide a description for the lore entry.',
            'entry_author': 'Enter the author name (optional).',
        }
        

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['entry_name'].label = "Entry Name"
        self.fields['entry_type'].label = "Entry Type"
        self.fields['entry_description'].label = "Entry Description"
        self.fields['entry_author'].label = "Entry Author"

    def clean_entry_name(self):
        entry_name = self.cleaned_data.get('entry_name')
        if not entry_name:
            return entry_name

        duplicates = LoreEntry.objects.filter(entry_name=entry_name)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("A lore entry with this name already exists.")
        return entry_name