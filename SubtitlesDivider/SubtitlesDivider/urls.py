"""
Definition of urls for SubtitlesDivider.
"""
from django.conf.urls.static import static
from datetime import datetime
from django.conf.urls import url
import django.contrib.auth.views
from django.conf import settings
import app.forms
from app import views

urlpatterns = [
    url(r'^$', views.upload_multiple_files, name='basic_upload'),
    url('download_zip/', views.download_zip, name='download_zip'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)