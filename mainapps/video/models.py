
from django.db import models
from mainapps.accounts.models import User

class Video(models.Model):
    title = models.CharField(max_length=255)
    video_file = models.FileField(upload_to='videos/')
    duration = models.FloatField(help_text="Duration in seconds")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='videos')

    def __str__(self):
        return self.title

class ProcessedVideo(models.Model):
    original_video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='processed_videos')
    final_video = models.FileField(upload_to='processed_videos/')
    processed_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='processed_videos')

    def __str__(self):
        return f'Processed - {self.original_video.title}'

class VideoProcessingTask(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    task_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Task {self.task_id} for video {self.video.title}'



class ClipCategory(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='categories')

    def __str__(self):
        return self.name

class VideoClip(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,null=True,blank=True,editable=False, related_name='user_clips')

    title = models.CharField(max_length=255, null=True, blank=True)
    video_file = models.FileField(upload_to='video_clips/')
    duration = models.FloatField(null=True, blank=True)  # You can extract this with MoviePy when uploading the clip
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(ClipCategory,null=True,on_delete=models.SET_NULL, related_name='video_clips', blank=True)
    is_favorite = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title or 'Untitled'}"

