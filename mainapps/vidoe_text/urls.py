from django.urls import path
from .views import *

app_name='video_text'
urlpatterns=[
    path('add_text/',add_text,name='add_text')
]