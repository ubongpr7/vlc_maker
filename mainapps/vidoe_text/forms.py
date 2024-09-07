from django import forms
from .models import TextFile
class TextFileForm(forms.ModelForm):
    # Resolution Options
    RESOLUTION_CHOICES = [
        ('1:1', 'FB/IG feed'),
        ('16:9', 'YouTube'),
    ]
    resolution = forms.ChoiceField(choices=RESOLUTION_CHOICES, initial='1:1')
    class Meta:
        model =TextFile
        fields='__aLL__'