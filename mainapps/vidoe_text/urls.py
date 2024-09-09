from django.urls import path
from .views import *

app_name='video_text'
urlpatterns=[
    path('',add_text,name='add_text'),
    path('process-textfile/<str:textfile_id>/', process_textfile, name='process_textfile'),

]