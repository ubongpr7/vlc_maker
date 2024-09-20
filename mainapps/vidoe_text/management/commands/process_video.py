from django.core.management.base import BaseCommand
from mainapps.vidoe_text.models import TextFile  
import sys
import time




from pathlib import Path
from moviepy.editor import (
    AudioFileClip, ColorClip, CompositeVideoClip, concatenate_videoclips, CompositeAudioClip,
    TextClip, VideoFileClip
)
import moviepy.video.fx.resize as rz
from moviepy.video.fx.crop import crop
from moviepy.video.fx.loop import loop
from moviepy.config import change_settings
import openai
import requests
import shutil


from moviepy.video.fx.speedx import speedx
from elevenlabs import Voice, VoiceSettings, play, save as save_11
from elevenlabs.client import ElevenLabs
import subprocess
import json
import sys
import moviepy.video.fx.all as vfx
import logging
import warnings
from pydantic import BaseModel, ConfigDict, Field
import os 
import re
import json
from typing import List, Dict
import pysrt
from pysrt import  SubRipTime,SubRipFile,SubRipItem

import time
from django.utils import timezone
from django.conf import settings


base_path = settings.MEDIA_ROOT


# Suppress specific Pydantic warnings
warnings.filterwarnings("ignore", category=UserWarning, )


openai.api_key = 'sk-proj-mo9iZjhl3DNjXlxMcx1FT3BlbkFJz5UCGoPBLnSQhh2b2stB' # write your openai api
PEXELS_API_KEY = 'ljSCcK6YYuU0kNyMTADStB8kSOWdkzHCZnPXc26QEHhaHYqeXusdnzaA' # write your pexels
# Base URL for Pexels API
BASE_URL = 'https://api.pexels.com/videos/search'
os.environ['PYTHONIOENCODING'] = 'UTF-8'

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
imagemagick_path = "/usr/bin/convert" # Set the path to the ImageMagick executable
os.environ['IMAGEMAGICK_BINARY'] = imagemagick_path
change_settings({"IMAGEMAGICK_BINARY": imagemagick_path})








class Command(BaseCommand):
    help = 'Process video files based on TextFile model'

    def add_arguments(self, parser):
        parser.add_argument('text_file_id', type=int)

    def handle(self, *args, **kwargs):
        text_file_id = kwargs['text_file_id']
        text_file_instance = TextFile.objects.get(id=text_file_id)

        text_file=text_file_instance.text_file
        voice_id=text_file_instance.voice_id
        api_key=text_file_instance.api_key
    
        timestamp = int(time.time())

        output_audio_file = os.path.join(base_path, 'text_audio', f'{timestamp}_{text_file_id}_audio.mp3')

        audio_file = self.convert_text_to_speech(text_file, voice_id, api_key,output_audio_file) #this is a file path
        print(f'audio_file: ',audio_file)
        text_file_instance.generated_audio=output_audio_file
        text_file_instance.save()

        self.stdout.write(self.style.SUCCESS(f'Processing complete for {text_file_id}.'))
    

    def convert_text_to_speech(self,text_file_path, voice_id, api_key, output_audio_file):
        """
        Converts a text file to speech using ElevenLabs and saves the audio in the specified output directory.
        
        Args:
            text_file_path (str): Path to the text file.
            voice_id (str): The voice ID for speech synthesis.
            api_key (str): API key for ElevenLabs authentication.
            output_audio_file (str): Path where the output audio file will be saved.
            
        Returns:
            str: Path to the generated audio file or None if an error occurred.
        """
        try:
            # Read the text from the file
            # with open(text_file_path, "r") as text_file:
            with text_file_path.open('r') as f:
            
                text = f.read().strip()
                print(text)
            
            # Initialize the ElevenLabs client
            client = ElevenLabs(api_key=api_key)
            
            # Generate speech from the text using the specified voice
            audio_data_generator = client.generate(
                text=text,
                voice=Voice(
                    voice_id=voice_id,
                    settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
                )
            )

            # Convert the generator to bytes
            audio_data = b''.join(audio_data_generator)

            # Check if the output file already exists and delete it
            if os.path.exists(output_audio_file):
                os.remove(output_audio_file)

            # Create the necessary directories if they do not exist
            os.makedirs(os.path.dirname(output_audio_file), exist_ok=True)
            
            # Save the generated audio to a file
            with open(output_audio_file, 'wb') as audio_file:
                audio_file.write(audio_data)

            logging.info(f"Audio file saved successfully: {output_audio_file}")
            return output_audio_file  # Return the path to the saved audio file

        except FileNotFoundError:
            logging.error("Error: The specified text file was not found.")
        except Exception as e:
            logging.error(f"An unexpected error occurred: {e}")
        
        return None  # Return None if an error occurred
