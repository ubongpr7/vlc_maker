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

from django.core.files.base import ContentFile

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
import os
import subprocess
import logging
import tempfile
from django.core.files.base import ContentFile

import time
from django.utils import timezone
from django.conf import settings
import boto3


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






def parse_s3_url(s3_url):
    """
    Parse the S3 URL to extract the bucket name and the key.
    
    Args:
        s3_url (str): The S3 URL (e.g., s3://mybucket/myfile.txt)
        
    Returns:
        tuple: (bucket_name, key)
    """
    s3_url = s3_url.replace("s3://", "")
    bucket_name, key = s3_url.split('/', 1)
    return bucket_name, key


def download_from_s3(s3_url, local_file_path):
    """
    Download a file from S3 to a local path.
    
    Args:
        s3_url (str): S3 URL of the file.
        local_file_path (str): Local path to save the downloaded file.
        
    Returns:
        bool: True if successful, False otherwise.
    """
    s3 = boto3.client('s3')

    # Parse the S3 URL to get the bucket name and key
    bucket_name, key = parse_s3_url(s3_url)
    
    try:
        s3.download_file(bucket_name, key, local_file_path)
        logging.info(f'File downloaded successfully from {s3_url} to {local_file_path}')
        return True
    except Exception as e:
        logging.error(f'Error downloading file from S3: {e}')
        return False

timestamp = int(time.time())

class Command(BaseCommand):
    help = 'Process video files based on TextFile model'

    def add_arguments(self, parser):
        parser.add_argument('text_file_id', type=int)

    def handle(self, *args, **kwargs):
        text_file_id = kwargs['text_file_id']
        text_file_instance = TextFile.objects.get(id=text_file_id)
        self.text_file_instance = TextFile.objects.get(id=text_file_id)
        text_file=text_file_instance.text_file
        voice_id=text_file_instance.voice_id
        api_key=text_file_instance.api_key
    

        output_audio_file = os.path.join(base_path,'audio',f'{timestamp}_{text_file_id}_audio.mp3')

        audio_file = self.convert_text_to_speech(text_file, voice_id, api_key,output_audio_file) #this is a file path
        # print(f'audio_file: ',audio_file)
        # text_file_instance.generated_audio=audio_file
        # text_file_instance.save()
        logging.info('done with audio file ')
        output_srt_file_path = os.path.join(base_path, 'srt_files', f'{text_file_id}_generated_srt_output.json')

        # srt_file_path = self.generate_srt_file(audio_file, text_file, output_srt_file_path)
        if audio_file:

            srt_file=self.generate_srt_file()
        else:
            return
        logging.info('done with srt_file')
        self.stdout.write(self.style.SUCCESS(f'Processing complete for {text_file_id}.'))
    

    
    # def generate_srt_file(self,audio_file_path, text_file_path, output_srt_file_path):
    #     """
    #     Generates an SRT file using Aeneas from the provided text and audio file paths.
    #     """
    #     # Aeneas command to generate SRT
    #     os.makedirs(os.path.dirname(output_srt_file_path), exist_ok=True)
    #     command = f'python3.10 -m aeneas.tools.execute_task "{audio_file_path}" "{text_file_path}" ' \
    #             f'"task_language=eng|is_text_type=plain|os_task_file_format=json" "{output_srt_file_path}"'

    #     try:
    #         # Run the command using subprocess
    #         logging.info(f'Running command: {command}')
    #         result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    #         # Log command output
    #         logging.info(f'Command output: {result.stdout}')

    #         # Check for errors in subprocess execution
    #         if result.returncode == 0:
    #             logging.info(f'SRT file generated successfully: {output_srt_file_path}')
    #             return output_srt_file_path  # Return the path of the generated SRT file
    #         else:
    #             logging.error(f'Error generating SRT file: {result.stderr}')
    #             return None
    #     except Exception as e:
    #         logging.error(f'An unexpected error occurred while generating SRT file: {e}')
    #         return None
    

    def convert_text_to_speech(self, text_file_path, voice_id, api_key, output_audio_file):
        """
        Converts a text file to speech using ElevenLabs and saves the audio in the specified output directory.
        
        Args:
            text_file_path (str): Path to the text file.
            voice_id (str): The voice ID for speech synthesis.
            api_key (str): API key for ElevenLabs authentication.
            output_audio_file (str): Path where the output audio file will be saved.
            
        Returns:
            str: Presigned URL of the uploaded audio file or None if an error occurred.
        """
        try:
            # Read the text from the file
            with text_file_path.open('r') as f:
                text = f.read().strip()
                logging.info(f'Read text for TTS: {text[:50]}...')  # Log first 50 characters
            
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


        # Instead of manually saving the file, save it using Django's FileField
 # Check if the generated_audio field already contains a file, and delete it if it does
            if self.text_file_instance.generated_audio:
                self.text_file_instance.generated_audio.delete(save=False)  # Delete the old file, don't save yet

            # Create a new file name for the audio (no leading /)
            audio_file_name = f"{timestamp}_{self.text_file_instance.id}_audio.mp3"

            # Save the new file to Django's FileField (linked to S3 storage)
            self.text_file_instance.generated_audio.save(audio_file_name, ContentFile(audio_data))

        # Return the URL to
            return self.text_file_instance.generated_audio  # This will return the URL managed by Django's FileField
        except Exception as e:
            print(e)
            return None
        


    def generate_srt_file(self):
        """
        Generate an SRT file from audio and text stored in S3, and save it to the TextFile instance.
        
        Args:
            text_file_instance: The TextFile instance containing audio and text file paths.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        text_file_instance=self.text_file_instance
        s3_audio_url = text_file_instance.audio_file.url
        s3_text_url = text_file_instance.text_file.url

        # Create temporary files to store downloaded audio and text files
        with tempfile.NamedTemporaryFile(suffix=".mp3") as temp_audio, tempfile.NamedTemporaryFile(suffix=".txt") as temp_text:
            # Download audio file from S3 to local temporary file
            if not download_from_s3(s3_audio_url, temp_audio.name):
                return False

            # Download text file from S3 to local temporary file
            if not download_from_s3(s3_text_url, temp_text.name):
                return False

            # Run the aeneas command to generate SRT
            command = f'python3.10 -m aeneas.tools.execute_task "{temp_audio.name}" "{temp_text.name}" ' \
                    f'"task_language=eng|is_text_type=plain|os_task_file_format=srt"'

            try:
                logging.info(f'Running command: {command}')
                result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                # Log command output
                logging.info(f'Command output: {result.stdout}')
                logging.error(f'Command error (if any): {result.stderr}')

                # Check for errors in subprocess execution
                if result.returncode == 0:
                    logging.info(f'SRT content generated successfully')

                    # Save the SRT content to the TextFile instance's srt_file field
                    srt_content = result.stdout  # Capturing the generated SRT content
                    srt_file_name = f"{text_file_instance.id}_generated.srt"

                    # If there is an existing file, delete it first
                    if text_file_instance.srt_file:
                        text_file_instance.srt_file.delete(save=False)

                    # Save the new SRT content to the srt_file field
                    text_file_instance.srt_file.save(srt_file_name, ContentFile(srt_content))

                    logging.info(f'SRT file saved to instance: {srt_file_name}')
                    return True
                else:
                    logging.error(f'Error generating SRT file: {result.stderr}')
                    return False
            except Exception as e:
                logging.error(f'An unexpected error occurred while generating the SRT file: {e}')
                return False
