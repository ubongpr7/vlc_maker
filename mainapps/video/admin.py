from django.contrib import admin
from .models import Video,VideoProcessingTask,ProcessedVideo
# Register your models here.

admin.site.register(VideoProcessingTask)
admin.site.register(Video)
admin.site.register(ProcessedVideo)
