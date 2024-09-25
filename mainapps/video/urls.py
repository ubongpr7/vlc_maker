from django.urls import path
from .views import *

app_name='video'
urlpatterns=[
    path('add-scene/<str:textfile_id>/',add_video_clips,name='add_scenes'),
    path('get_clip/<str:cat_id>/',get_clip,name='get_clip'),
    path('upload-folder/',upload_video_folder,name='upload_video_folder'),
    path('assets/<str:category_id>/',category_view,name='subcategory_view'),
    path('assets/', category_view, name='category_view'),
    path('assets/<str:category_id>/<str:video_id>/', category_view, name='category_view_video'),
    path('categories/delete/<int:category_id>/', delete_category, name='delete_category'),
    path('clips/delete/<int:clip_id>/', delete_clip, name='delete_video'),

]

