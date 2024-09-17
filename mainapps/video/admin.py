from django.contrib import admin
from .models import Video,VideoProcessingTask,ProcessedVideo,VideoClip,ClipCategory
# Register your models here.
from django.contrib import admin

admin.site.register(VideoProcessingTask)
admin.site.register(VideoClip)
admin.site.register(ClipCategory)
admin.site.register(Video)
admin.site.register(ProcessedVideo)



@admin.register(ClipCategory)
class ClipCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'user')

@admin.register(VideoClip)
class VideoClipAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'created_at')
