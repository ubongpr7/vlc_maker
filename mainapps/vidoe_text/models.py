import logging
import os
import uuid
from django.db import models
from django.core.exceptions import ValidationError
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
import pysrt

from pathlib import Path
from typing import List, Dict
import os
import re

from django.core.files import File
from django.conf import settings

MAINRESOLUTIONS = {
    '1:1': 1/1,
    '16:9': 16/9,
    '4:5': 4/5,
    '9:16': 9/16
}

RESOLUTIONS = {
    '16:9': (1920, 1080),
    '4:3': (1440, 1080),
    '1:1': (1080, 1080),
    # Add other resolutions if needed
}


allow_population_by_field_name = True
populate_by_name = True


def text_file_upload_path(instance, filename):
    """Generate a unique file path for each uploaded text file."""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'  # Use UUID to ensure unique file names
    if instance.id:
        return os.path.join('text_files', 'new', filename)
    return os.path.join('text_files', filename)

def font_file_upload_path(instance, filename):
    """Generate a unique file path for uploaded custom fonts."""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join('fonts', filename)

def audio_file_upload_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join('audio', filename)




def subriptime_to_seconds(srt_time: pysrt.SubRipTime) -> float:
    return srt_time.hours * 3600 + srt_time.minutes * 60 + srt_time.seconds + srt_time.milliseconds / 1000.0



class AudioClip(models.Model):
    audio_file = models.FileField(upload_to='audio_clips/')
    duration = models.FloatField(null=True, blank=True)  # Duration in seconds
    voice_id = models.CharField(max_length=255)

class TextFile(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,null=True,editable=False)

    text_file = models.FileField(upload_to=text_file_upload_path,null=True,blank=True)
    voice_id = models.CharField(max_length=100)
    api_key = models.CharField(max_length=200)
    resolution = models.CharField(max_length=50)
    font_file = models.FileField(upload_to=font_file_upload_path, blank=True, null=True)
    font_color = models.CharField(max_length=7)  # e.g., hex code: #ffffff
    subtitle_box_color = models.CharField(max_length=7, blank=True, null=True)
    font_size = models.IntegerField()
    audio_file = models.FileField(upload_to='audio_files', blank=True, null=True)
    srt_file = models.FileField(upload_to='srt_files/', blank=True, null=True)  # SRT file for subtitles
    blank_video = models.FileField(upload_to='blank_video/', blank=True, null=True) 
    subtitle_file = models.FileField(upload_to='subtitles/', blank=True, null=True)
    fps = models.IntegerField(default=30,editable=False)
    def clean(self):
        """Validate color fields and font size during model validation."""
        if not (1 <= self.font_size <= 100):
            raise ValidationError("Font size must be between 1 and 100.")
        if not self.is_valid_hex_color(self.font_color):
            raise ValidationError("Invalid hex color for font_color.")
        if not self.is_valid_hex_color(self.subtitle_box_color):
            raise ValidationError("Invalid hex color for subtitle_box_color.")

    @staticmethod
    def is_valid_hex_color(color_code):
        """Validate if a color code is a valid hex value."""
        if len(color_code) != 7 or color_code[0] != '#':
            return False
        try:
            int(color_code[1:], 16)
            return True
        except ValueError:
            return False
    
    def process_text_file(self):
        """Process the uploaded text file and return lines stripped of extra spaces."""
        if not self.text_file:
            raise FileNotFoundError("No text file has been uploaded.")
        
        try:
            # with self.text_file.open() as f: 
            with open(self.text_file.path, 'r') as f:
                lines = f.readlines()
            return [line.strip() for line in lines if line.strip()]
        except IOError as e:
            raise IOError(f"Error processing file: {e}")

    def __str__(self):
        return self.voice_id
        
def text_clip_upload_path(instance, filename):
    """Generate a unique file path for each uploaded text file."""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'  # Use UUID to ensure unique file names
    if instance.id:
        return os.path.join('text_files', 'new', filename)
    return os.path.join('text_clip', str(instance.id), filename)

class TextLineVideoClip(models.Model):
    text_file = models.ForeignKey(TextFile, on_delete=models.CASCADE, related_name='video_clips')
    video_file = models.ForeignKey('video.VideoClip', on_delete=models.SET_NULL, null=True, related_name='usage')
    video_file_path = models.FileField(upload_to=text_clip_upload_path)
    line_number = models.IntegerField()  # Corresponds to the line number in the text file
    timestamp_start = models.FloatField(null=True, blank=True)  # Start time for where this clip begins in the final video
    timestamp_end = models.FloatField(null=True, blank=True)  # End time for where this clip ends in the final video
    
    def to_dict(self):
        if self.video_file:
            video_path=self.video_file.video_file
        else:
            video_path = self.video_file_path if self.video_file_path else ''  # Fallback to empty string if not available

        return {
            "line_number": self.line_number,
            "video_path": video_path.path,
            "timestamp_start": self.timestamp_start,
            "timestamp_end": self.timestamp_end
        }
    def __str__(self):
        return f"VideoClip for line {self.line_number} of {self.text_file}"

    class Meta:
        # Add unique constraint on text_file and line_number
        unique_together = ('text_file', 'line_number')
        
        # Set default ordering by line_number, then by text_file
        ordering = ['line_number', 'text_file']
