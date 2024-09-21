from django.core.management.base import BaseCommand
from mainapps.vidoe_text.models import TextFile, TextLineVideoClip  
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


# Predefined resolutions
RESOLUTIONS = {
    '1:1': (480, 480),
    '16:9': (1920, 1080),
    '4:5': (800, 1000),
    '9:16': (1080, 1920)
}

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

AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
bucket_name = settings.AWS_STORAGE_BUCKET_NAME
aws_secret = settings.AWS_SECRET_ACCESS_KEY
s3 = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=aws_secret)

def download_from_s3(file_key, local_file_path):
    """
    Download a file from S3 and save it to a local path.
    
    Args:
        file_key (str): The S3 object key (file path in the bucket).
        local_file_path (str): The local file path where the file will be saved.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        # Download the file from the bucket using its S3 object key
        response=s3.get_object(Bucket=bucket_name, Key=file_key)
        object_content = response['Body'].read()
        logging.info(f"Downloaded {file_key} from S3 to {local_file_path}")
        return object_content
    except Exception as e:
        logging.error(f"Failed to download {file_key} from S3: {e}")
        return False

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

s3_client = boto3.client('s3')

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

            srt_file=self.generate_srt_file('g')
            
        else:
            return
        aligned_output=self.process_srt_file('g')
        blank_video=self.generate_blank_video_with_audio()
        print('aligned_output: ',aligned_output)
        text_clips= TextLineVideoClip.objects.filter(text_file=self.text_file_instance)
        num_segments=len(text_clips)
        self.stdout.write(self.style.SUCCESS(f'Processing complete for {text_file_id}.'))
    


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
        

    def convert_time(self,seconds):
        milliseconds = int((seconds - int(seconds)) * 1000)
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"


    def generate_srt_file(self,f):
        """
        Download the audio and text files from S3, and process them using a subprocess.
        """
        text_file_instance = self.text_file_instance
        
        # Extract the S3 bucket and file key from the audio and text files
        s3_text_url = text_file_instance.text_file.name  # This gives the S3 key (path within the bucket)
        s3_audio_url = text_file_instance.generated_audio.name  # This gives the S3 key (path within the bucket)

        logging.info(f"Downloading audio from S3: {s3_audio_url}")
        logging.info(f"Downloading text from S3: {s3_text_url}")
        
        # Ensure file paths are not empty
        if not s3_audio_url or not s3_text_url:
            logging.error("Audio or text file path from S3 is empty")
            return False
        
        # Create temporary files to store downloaded audio, text, and SRT files
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio, \
            tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_text, \
            tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_srt:

            # Download the audio file from S3 and write it to the temp file
            audio_content = download_from_s3(s3_audio_url, temp_audio.name)
            if not audio_content:
                logging.error(f"Failed to download audio file {s3_audio_url}")
                return False
            
            # Write the audio content to the temporary audio file
            with open(temp_audio.name, 'wb') as audio_file:
                audio_file.write(audio_content)
            
            # Download the text file from S3 and write it to the temp file
            text_content = download_from_s3(s3_text_url, temp_text.name)
            if not text_content:
                logging.error(f"Failed to download text file {s3_text_url}")
                return False
            
            # Write the text content to the temporary text file
            with open(temp_text.name, 'wb') as text_file:
                text_file.write(text_content)
            
            # Run the subprocess to generate SRT using Aeneas or other tool
            command = f'python3.10 -m aeneas.tools.execute_task "{temp_audio.name}" "{temp_text.name}" ' \
                    f'"task_language=eng|is_text_type=plain|os_task_file_format=json" "{temp_srt.name}"'

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
                    with open(temp_srt.name, 'rb') as srt_file:
                        srt_content = srt_file.read()
                    
                    srt_file_name = f"{text_file_instance.id}_generated.json"

                    # If there is an existing SRT file, delete it first
                    if text_file_instance.generated_srt:
                        text_file_instance.generated_srt.delete(save=False)

                    # Save the new SRT content to the srt_file field
                    text_file_instance.generated_srt.save(srt_file_name, ContentFile(srt_content))

                    logging.info(f'SRT file saved to instance: {srt_file_name}')
                    return text_file_instance.generated_srt
                else:
                    logging.error(f'Error generating SRT file: {result.stderr}')
                    return False
            except Exception as e:
                logging.error(f'An unexpected error occurred while generating the SRT file: {e}')
                return False


    def process_srt_file(self,f):
        """
        Downloads the generated SRT file from S3, processes it, and returns the aligned output.
        
        Args:
            text_file_instance: The instance containing the S3 path to the generated SRT file.
            
        Returns:
            list: A list of formatted SRT entries.
        """
        text_file_instance=self.text_file_instance
        s3_srt_key = text_file_instance.generated_srt.name  # S3 key (SRT file path in the bucket)

        if not s3_srt_key:
            logging.error("SRT file path from S3 is empty")
            return None
        
        logging.info(f"Downloading SRT file from S3: {s3_srt_key}")
        
        # Create a temporary file to hold the downloaded SRT content
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_srt:
            srt_content = download_from_s3(s3_srt_key, temp_srt.name)
            
            if not srt_content:
                logging.error(f"Failed to download SRT file {s3_srt_key}")
                return None
            
            # Write the SRT content to the temporary file
            with open(temp_srt.name, 'wb') as srt_file:
                srt_file.write(srt_content)
            
            # Load and process the SRT file
            try:
                with open(temp_srt.name, 'r') as f:
                    sync_map = json.load(f)

                aligned_output = []
                for index, fragment in enumerate(sync_map['fragments']):
                    start = self.convert_time(float(fragment['begin']))
                    end = self.convert_time(float(fragment['end']))
                    text = fragment['lines'][0].strip()
                    
                    # Format the SRT entry
                    aligned_output.append(f"{index + 1}\n{start} --> {end}\n{text}\n")
                
                logging.info('Finished processing the SRT file')
                return aligned_output
            
            except Exception as e:
                logging.error(f"Error processing SRT file: {e}")
                return None



    def generate_blank_video_with_audio(self):
        """
        Generate a blank video with audio and save the result.

        Returns:
            bool: True if successful, False otherwise.
        """
        text_file_instance = self.text_file_instance
        try:
            # Get the resolution from text_file_instance
            resolution = text_file_instance.resolution
            if resolution not in RESOLUTIONS:
                raise ValueError(f"Resolution '{resolution}' is not supported. Choose from {list(RESOLUTIONS.keys())}.")
            width, height = RESOLUTIONS[resolution]

            # Download the audio file from S3
            audio_s3_key = text_file_instance.generated_audio.name
            srt_s3_key = text_file_instance.generated_srt.name
            if not audio_s3_key or not srt_s3_key:
                logging.error("Audio or SRT file path from S3 is empty.")
                return False

            # Create temporary files for audio and SRT
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio, \
                    tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_srt, \
                    tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_output_video:

                # Download the audio and SRT files from S3
                audio_content = download_from_s3(audio_s3_key, temp_audio.name)
                srt_content = download_from_s3(srt_s3_key, temp_srt.name)

                if not audio_content or not srt_content:
                    logging.error("Failed to download audio or SRT file from S3.")
                    return False

                # Write the contents to the temp files
                with open(temp_audio.name, 'wb') as audio_file, open(temp_srt.name, 'wb') as srt_file:
                    audio_file.write(audio_content)
                    srt_file.write(srt_content)

                # Load the SRT file and calculate duration
                srt_duration = self.get_video_duration_from_json(temp_srt.name)

                # Load the audio file and calculate duration
                audio_clip = AudioFileClip(temp_audio.name)
                audio_duration = audio_clip.duration

                # Log the calculated durations
                logging.info(f"Audio duration: {audio_duration}, SRT duration: {srt_duration}")

                # Determine the maximum duration between the SRT and audio file
                duration = max(srt_duration, audio_duration)
                if duration == 0:
                    logging.error("Duration is zero, cannot create a video.")
                    return False

                # Log the video creation process
                logging.info(f"Creating a blank video with resolution {width}x{height} and duration {duration}")

                # Create a blank (black) video clip with the specified resolution and duration
                blank_clip = ColorClip(size=(width, height), color=(0, 0, 0)).set_duration(duration)

                # Combine the audio with the blank video
                final_video = CompositeVideoClip([blank_clip]).set_audio(audio_clip)

                # Write the final video to the temporary output file
                final_video.write_videofile(temp_output_video.name, fps=30)

                # Save the final video to the `text_file_instance`
                if text_file_instance.generated_blank_video:
                    text_file_instance.generated_blank_video.delete(save=False)

                # Save the video content correctly
                with open(temp_output_video.name, 'rb') as output_video_file:
                    video_content = output_video_file.read()

                text_file_instance.generated_blank_video.save(f"blank_output_{text_file_instance.id}.mp4", ContentFile(video_content))

                logging.info(f"Video generated successfully and saved as {text_file_instance.generated_blank_video.name}")
                return text_file_instance.generated_blank_video

        except Exception as e:
            logging.error(f"Error generating video: {e}")
            return False

    # def generate_blank_video_with_audio(self):
    #     """
    #     Generate a blank video with audio and save the result.
        
    #     Args:
    #         text_file_instance: The instance containing the S3 paths for the audio and SRT files,
    #                             as well as the desired resolution.
                                
    #     Returns:
    #         bool: True if successful, False otherwise.
    #     """
    #     text_file_instance=self.text_file_instance
    #     try:
    #         # Get the resolution from text_file_instance
    #         resolution = text_file_instance.resolution
    #         if resolution not in RESOLUTIONS:
    #             raise ValueError(f"Resolution '{resolution}' is not supported. Choose from {list(RESOLUTIONS.keys())}.")
    #         width, height = RESOLUTIONS[resolution]

    #         # Download the audio file from S3
    #         audio_s3_key = text_file_instance.generated_audio.name
    #         srt_s3_key = text_file_instance.generated_srt.name
    #         if not audio_s3_key or not srt_s3_key:
    #             logging.error("Audio or SRT file path from S3 is empty.")
    #             return False

    #         # Create temporary files for audio and SRT
    #         with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio, \
    #             tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_srt, \
    #             tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_output_video:

    #             # Download the audio and SRT files from S3
    #             audio_content = download_from_s3(audio_s3_key, temp_audio.name)
    #             srt_content = download_from_s3(srt_s3_key, temp_srt.name)
                
    #             if not audio_content or not srt_content:
    #                 logging.error("Failed to download audio or SRT file from S3.")
    #                 return False

    #             # Write the contents to the temp files
    #             with open(temp_audio.name, 'wb') as audio_file, open(temp_srt.name, 'wb') as srt_file:
    #                 audio_file.write(audio_content)
    #                 srt_file.write(srt_content)

    #             # Load the SRT file and calculate duration
    #             srt_duration = self.get_video_duration_from_json(temp_srt.name)

    #             # Load the audio file and calculate duration
    #             audio_clip = AudioFileClip(temp_audio.name)
    #             audio_duration = audio_clip.duration

    #             # Determine the maximum duration between the SRT and audio file
    #             duration = max(srt_duration, audio_duration)

    #             # Create a blank (black) video clip with the specified resolution and duration
    #             blank_clip = ColorClip(size=(width, height), color=(0, 0, 0)).set_duration(duration)

    #             # Combine the audio with the blank video
    #             final_video = CompositeVideoClip([blank_clip]).set_audio(audio_clip)

    #             # Write the final video to the temporary output file
    #             final_video.write_videofile(temp_output_video.name, fps=30)

    #             # Save the final video to the `text_file_instance`
    #                                 # If there is an existing SRT file, delete it first
    #             if text_file_instance.generated_blank_video:
    #                 text_file_instance.generated_blank_video.delete(save=False)

    #             # Save the new SRT content to the srt_file field
    #             text_file_instance.generated_blank_video.save(f"blank_output_{text_file_instance.id}.mp4", ContentFile(temp_output_video.name))

    #             logging.info(f"Video generated successfully and saved as {text_file_instance.video_file.name}")
    #             return text_file_instance.generated_blank_video

    #     except Exception as e:
    #         logging.error(f"Error generating video: {e}")
    #         return False

    def get_video_duration_from_json(self,json_file):
        with open(json_file, 'r') as file:
            data = json.load(file)

        # Extract the end times from the fragments
        end_times = [fragment['end'] for fragment in data['fragments']]

        # Get the last end time (duration of the video)
        last_end_time = end_times[-1] if end_times else "0.000"

        # Convert the time format (seconds) to float
        return float(last_end_time)
