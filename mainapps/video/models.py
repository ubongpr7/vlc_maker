import os
import uuid
from django.db import models

def video_upload_path(instance, filename):
    """Generate a unique file path for each uploaded video file."""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'  # Use a UUID for the filename
    return os.path.join('videos', str(instance.id), filename)

def music_upload_path(instance, filename):
    """Generate a unique file path for each uploaded background music file."""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'  # Use a UUID for the filename
    return os.path.join('background_music', str(instance.id), filename)

def text_file_upload_path(instance, filename):
    """Generate a unique file path for each uploaded text file."""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'  # Use a UUID for the filename
    return os.path.join('text_files', str(instance.id), filename)

def processed_video_upload_path(instance, filename):
    """Generate a unique file path for each processed video."""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'  # Use a UUID for the filename
    return os.path.join('processed_videos', str(instance.id), filename)

# Models
class Video(models.Model):
    title = models.CharField(max_length=255, unique=True)
    video_file = models.FileField(upload_to=video_upload_path)  # Custom upload path
    duration = models.FloatField(help_text="Duration in seconds")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class BackgroundMusic(models.Model):
    title = models.CharField(max_length=255)
    music_file = models.FileField(upload_to=music_upload_path)  # Custom upload path
    start_time = models.FloatField(help_text="Start time in seconds")
    end_time = models.FloatField(help_text="End time in seconds")
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='background_music')

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(end_time__gte=models.F('start_time')), name="end_time_gte_start_time"),
        ]

    def __str__(self):
        return self.title

class TextFile(models.Model):
    title = models.CharField(max_length=255)
    text_file = models.FileField(upload_to=text_file_upload_path)  # Custom upload path
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='text_files')
    processed = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class ProcessedVideo(models.Model):
    original_video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='processed_videos')
    final_video = models.FileField(upload_to=processed_video_upload_path)  # Custom upload path
    processed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Processed - {self.original_video.title}'

class VideoProcessingTask(models.Model):
    video = models.ForeignKey(Video, on_delete=models.CASCADE)
    task_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    status = models.CharField(max_length=50, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Task {self.task_id} for video {self.video.title}'
