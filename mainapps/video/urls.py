from django.urls import path
from .views import *

app_name='video'
urlpatterns=[
    path('make_video/',make_video,name='video_maker')
]