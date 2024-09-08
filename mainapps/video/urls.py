from django.urls import path
from .views import *

app_name='video'
urlpatterns=[
    path('add-scene/<str:textfile_id>/',add_video_clips,name='add_scenes'),
    path('get_clip/<str:textfile_id>/',get_clip,name='get_clip'),
]