from django import forms
from .models import Board, Content, BoardContent

class BoardForm(forms.ModelForm):
    class Meta:
        model = Board
        fields = ['title', 'description', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Board title'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3, 'placeholder': 'Board description'}),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }

class ContentForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['file', 'content_type']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'class': 'form-input'}),
            'content_type': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super(ContentForm, self).__init__(*args, **kwargs)
        self.fields['content_type'].choices = [
            ('image', 'Image'),
            ('video', 'Video'),
            ('pdf', 'PDF'),
            ('doc', 'Document'),
            ('other', 'Other'),
        ]

class BoardContentForm(forms.ModelForm):
    class Meta:
        model = BoardContent
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter title'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'placeholder': 'Enter description', 'rows': 4}),
        }
