"""
Definition of forms.
"""

from django import forms
from app.models import MasterFiles,SubtitlesFiles


class UploadFileForm(forms.Form):
    #file = forms.FileField()
    files = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))
    #shortfiles = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))

class MasterForm(forms.ModelForm):
    class Meta:
        model=MasterFiles
        fields=('files',)
    pass

class SubtitleForm():
    class Meta:
        model=SubtitlesFiles
        fields=('shortfiles',)
    pass