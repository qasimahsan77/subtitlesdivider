"""
Definition of models.
"""

from django.db import models

class MasterFiles(models.Model):
    #title = models.CharField(max_length=255, blank=True)
    files = models.FileField(upload_to='MasterFiles/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class SubtitlesFiles(models.Model):
    #title = models.CharField(max_length=255, blank=True)
    files = models.FileField(upload_to='SubtitlesFiles/')
    uploaded_at = models.DateTimeField(auto_now_add=True)