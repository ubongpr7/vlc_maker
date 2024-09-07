# backgroundmusic/models.py

from django.db import models
from mainapps.video.models import Video

class BackgroundMusic(models.Model):
    title = models.CharField(max_length=255)
    music_file = models.FileField(upload_to='background_music/')
    start_time = models.FloatField(help_text="Start time in seconds")
    end_time = models.FloatField(help_text="End time in seconds")
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='background_music')

    def __str__(self):
        return self.title
