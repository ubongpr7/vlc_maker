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

class TextFile(models.Model):
    text_file = models.FileField(upload_to=text_file_upload_path, null=False, blank=False)
    voice_id = models.CharField(max_length=255, null=False, blank=False)  # ElevenLabs voice ID
    api_key = models.CharField(max_length=255, null=False, blank=False)  # ElevenLabs API key
    resolution = models.CharField(max_length=50, default='1:1')  # Video resolution
    font_file = models.FileField(upload_to=font_file_upload_path, null=True, blank=True)  # Custom font file (optional)
    font_color = models.CharField(max_length=7, default='#FFFFFF')  # Font color (hex code)
    subtitle_box_color = models.CharField(max_length=7, default='#000000')  # Subtitle box color (hex code)
    font_size = models.IntegerField(default=24)  # Font size for subtitles
    processed = models.BooleanField(default=False,editable=False)

    def __str__(self):
        return self

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
            with self.text_file.open() as f:
                lines = f.readlines()
            return [line.strip() for line in lines]
        except IOError as e:
            raise IOError(f"Error processing file: {e}")

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
