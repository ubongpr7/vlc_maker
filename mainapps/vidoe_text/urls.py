from django.urls import path
from .views import *
from django.urls import re_path

app_name='video_text'
urlpatterns=[
    path('',add_text,name='add_text'),
    path('process-textfile/<str:textfile_id>/', process_textfile, name='process_textfile'),
    path('download_video/<str:textfile_id>/', download_video, name='download_video'),
    path('progress_page/<str:al_the_way>/<str:text_file_id>', progress_page, name='progress_page'),
    path('progress/<str:text_file_id>/', progress, name='progress'),
    path('process-background-music/<str:textfile_id>/', process_background_music, name='process_background_music'),path('media/<str:file_name>/', serve_file, name='serve_file'),
    re_path(r'^media/(?P<file_key>.+)/(?P<textfile_id>\w+)/$', download_file_from_s3, name='download_file'),

    path('validate_api_key/',validate_api_keyv, name='validate_api_key'),

]