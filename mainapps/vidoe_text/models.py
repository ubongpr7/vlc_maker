import os
import uuid
from django.db import models
from django.core.exceptions import ValidationError

def text_file_upload_path(instance, filename):
    """Generate a unique file path for each uploaded text file."""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'  # Use UUID to ensure unique file names
    return os.path.join('text_files', str(instance.id), filename)

def font_file_upload_path(instance, filename):
    """Generate a unique file path for uploaded custom fonts."""
    ext = filename.split('.')[-1]
    filename = f'{uuid.uuid4()}.{ext}'
    return os.path.join('fonts', filename)


class AudioClip(models.Model):
    audio_file = models.FileField(upload_to='audio_clips/')
    duration = models.FloatField(null=True, blank=True)  # Duration in seconds
    voice_id = models.CharField(max_length=255)

class TextFile(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.SET_NULL,null=True,editable=False)

    text_file = models.FileField(upload_to=text_file_upload_path)
    voice_id = models.CharField(max_length=100)
    api_key = models.CharField(max_length=200)
    resolution = models.CharField(max_length=50)
    font_file = models.FileField(upload_to='fonts/', blank=True, null=True)
    font_color = models.CharField(max_length=7)  # e.g., hex code: #ffffff
    subtitle_box_color = models.CharField(max_length=7, blank=True, null=True)
    font_size = models.IntegerField()
    audio_file = models.FileField(upload_to=font_file_upload_path, blank=True, null=True)

    def __str__(self):
        return f"TextFile: {self.text_file.name}"
    def process_text_file(self):
        """Process the uploaded text file and return lines stripped of extra spaces."""
        if not self.text_file:
            raise FileNotFoundError("No text file has been uploaded.")
        
        try:
            with self.text_file.open() as f:
                lines = f.readlines()
            return [line.strip() for line in lines]
        except IOError as e:
            raise IOError(f"Error processing file: {e}")
    # def convert_text_to_speech(self):
    #     """
    #     Converts the entire text file to speech and saves the audio file.
    #     """
    #     import requests

    #     # Set ElevenLabs API key
    #     os.environ['ELEVENLABS_API_KEY'] = self.api_key

    #     # Read the text from the uploaded file
    #     with open(self.text_file.path, 'r') as file:
    #         text_data = file.read().strip()

    #     # Generate the audio using ElevenLabs
    #     try:
    #         audio = generate(
    #             text=text_data,
    #             voice=Voice(
    #                 voice_id=self.voice_id,
    #                 settings=VoiceSettings(
    #                     stability=0.71,
    #                     similarity_boost=0.5,
    #                     style=0.0,
    #                     use_speaker_boost=True
    #                 )
    #             )
    #         )
    #     except Exception as e:
    #         print(f"Error generating audio: {e}")
    #         return None

    #     # Save the audio file locally
    #     audio_filename = f"audio_{self.id}.mp3"
    #     audio_path = os.path.join(settings.MEDIA_ROOT, 'text_audio_files', audio_filename)
        
    #     # Ensure the directory exists
    #     os.makedirs(os.path.dirname(audio_path), exist_ok=True)

    #     try:
    #         eleven_save(audio, audio_path)
    #     except Exception as e:
    #         print(f"Error saving audio file: {e}")
    #         return None

    #     # Update the model's audio_file field
    #     self.audio_file = f"text_audio_files/{audio_filename}"
    #     self.save()

    #     return self.audio_file


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

  

    def save_font_file(self, font_file=None):
        """Save the uploaded font file or assign a default one."""
        if font_file:
            self.font_file.save(font_file.name, font_file)
        elif not self.font_file:
            default_font_path = os.path.join(os.getcwd(), 'data', 'Montserrat-SemiBold.ttf')
            self.font_file.save('Montserrat-SemiBold.ttf', open(default_font_path, 'rb'))
        
        self.save()

    def render_scenes(self):
        """Generate scene rendering data based on processed text and formatting options."""
        try:
            lines = self.process_text_file()
            return {
                'font_file': self.font_file.url if self.font_file else 'Montserrat-SemiBold.ttf',
                'margin': self.margin,
                'font_color': self.font_color,
                'font_size': self.font_size,
                'subtitle_box_color': self.subtitle_box_color,
                'lines': lines,
                'resolution': self.resolution,
            }
        except Exception as e:
            raise RuntimeError(f"Error rendering scenes: {e}")
        

class TextLineVideoClip(models.Model):

    text_file = models.ForeignKey(TextFile, on_delete=models.CASCADE, related_name='video_clips')
    video_file = models.ForeignKey('video.VideoClip', on_delete=models.SET_NULL, null=True, related_name='usage')
    video_file_path = models.FileField(upload_to='text_video_clips/')
    line_number = models.IntegerField()  # Corresponds to the line number in the text file
    timestamp_start = models.FloatField(null=True,blank=True)  # Start time for where this clip begins in the final video
    timestamp_end = models.FloatField(null=True,blank=True)  # End time for where this clip ends in the final video
    def __str__(self):
        return f"VideoClip for line {self.line_number} of {self.text_file}"
