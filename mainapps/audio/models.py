# backgroundmusic/models.py

import os
import uuid
from django.db import models
from mainapps.video.models import Video
from mainapps.vidoe_text.models import TextFile


class BackgroundMusic(models.Model):
    text_file=models.ForeignKey(TextFile, on_delete=models.CASCADE, related_name='background_musics')
    title = models.CharField(max_length=255,null=True,blank=True)
    music_file = models.FileField(upload_to='bg_music_file_upload_path')
    start_time = models.FloatField(help_text="Start time in seconds")
    end_time = models.FloatField(help_text="End time in seconds")
    # video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='background_music')

    def __str__(self):
        return self.title

