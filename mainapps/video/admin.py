from django.contrib import admin
from .models import Video,VideoProcessingTask,ProcessedVideo,VideoClip,ClipCategory
# Register your models here.

admin.site.register(VideoProcessingTask)
admin.site.register(VideoClip)
admin.site.register(ClipCategory)
admin.site.register(Video)
admin.site.register(ProcessedVideo)
