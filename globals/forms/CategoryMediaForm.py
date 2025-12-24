from django import forms
from ..models.CategoryMedia import CategoryMedia
from ..widgets.MultipleFileInput import MultipleFileInput

class CategoryMediaForm(forms.ModelForm):
    class Meta:
        model = CategoryMedia
        fields = ['file']
        widgets = {
            'file': MultipleFileInput(attrs={'multiple': True}),
        }
