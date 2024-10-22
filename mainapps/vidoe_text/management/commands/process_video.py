from django.core.management.base import BaseCommand
from mainapps.vidoe_text.models import TextFile, TextLineVideoClip ,LogoModel 
import sys
import time
import matplotlib.colors as mcolors
import imageio
from django.templatetags.static import static
from moviepy.editor import ImageClip
import numpy as np
from django.contrib.staticfiles.storage import staticfiles_storage
import textwrap
from PIL import ImageFont,Image
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
from process_video import replace_video_segments
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


fonts1={
    "Arial": os.path.join(os.getcwd(),'fonts','arial.ttf'),
    "Open Sans": os.path.join(os.getcwd(),'fonts','OpenSans-Semibold.ttf'),
    "Helvetica": os.path.join(os.getcwd(),'fonts','Helvetica.otf'),
    "Montserrat" :os.path.join(os.getcwd(),'fonts','montserra.ttf'),
    "Roboto" :os.path.join(os.getcwd(),'fonts','Roboto-Medium.ttf'),
}

fonts={
    "Arial": 'Arial',
    "Open Sans Condensed":'OpenSans-Semibold' ,
    "HelveticaforTarget-Bold": 'Helvetica-2',
    "Montserrat":'Montserrat',
    "Roboto Medium":'Roboto'
}



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
MAINRESOLUTIONS = {
    '1:1': 1/1,
    '16:9': 16/9,
    '4:5': 4/5,
    '9:16': 9/16
}
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
        resolution=text_file_instance.resolution
        self.text_file_instance.track_progress(2)
        


        voice_id=text_file_instance.voice_id
        api_key=text_file_instance.api_key
        audio_file=None
        # if not text_file_instance.generated_audio:
        output_audio_file = os.path.join(base_path,'audio',f'{timestamp}_{text_file_id}_audio.mp3')

        audio_file = self.convert_text_to_speech(text_file, voice_id, api_key,output_audio_file) #this is a file path
        if not audio_file:
            self.text_file_instance.track_progress('The Credit On Your ElevenLabs API Key Is Not Enough To Process The Text File')
            return 

        self.text_file_instance.track_progress(10)
        
        logging.info('done with audio file ')

        if audio_file or text_file_instance.generated_audio:

            srt_file=self.generate_srt_file()
            self.text_file_instance.track_progress(25)

            
        else:
            return
        aligned_output=self.process_srt_file()
        self.text_file_instance.track_progress(27)

        blank_video=self.generate_blank_video_with_audio()
        
        if blank_video:
            blank_vide_clip=self.load_video_from_file_field(self.text_file_instance.generated_blank_video)
            logging.info('Blank Video clip loaded')

        else:
            logging.error('Blank video file could not be loaded')
            self.text_file_instance.track_progress('error')

            return
        self.text_file_instance.track_progress(29)

        subtitles=self.load_subtitles_from_text_file_instance()
        self.text_file_instance.track_progress(32)

        print(subtitles)
        print('aligned_output: ',aligned_output)
        blank_video_segments, subtitle_segments = self.get_segments_using_srt(blank_vide_clip, subtitles)
        self.text_file_instance.track_progress(36)
        
        text_clips= TextLineVideoClip.objects.filter(text_file=self.text_file_instance)

        num_segments=len(text_clips)
        output_video_segments = []
        start = 0
        logging.info('output_video_segments is to start')
        for video_segment, new_subtitle_segment in zip(blank_video_segments, subtitles):
            end = self.subriptime_to_seconds(new_subtitle_segment.end)
            required_duration = end - start
            new_video_segment = self.adjust_segment_duration(video_segment, required_duration)
            
            output_video_segments.append(new_video_segment.without_audio())
            start = end
        self.text_file_instance.track_progress(39)
        
        replacement_video_files=self.get_video_paths_for_text_file()
        self.text_file_instance.track_progress(40)

        replacement_videos_per_combination=[]
        
        for replacement_video_file in replacement_video_files:
                replacement_video = self.load_video_from_file_field(replacement_video_file)
                cropped_replacement_video =  self.crop_to_aspect_ratio_(replacement_video, MAINRESOLUTIONS[text_file_instance.resolution]) #MAINRESOLUTIONS[resolution]
                
                logging.info(f"Replacement video {replacement_video_file} cropped to desired aspect ratio")
                if len(replacement_videos_per_combination) < len(replacement_video_files):
                    replacement_videos_per_combination.append({})
        logging.info('Concatination Done')
        self.text_file_instance.track_progress(48)

        
        final_blank_video = self.concatenate_clips(blank_video_segments,target_resolution=MAINRESOLUTIONS[text_file_instance.resolution],target_fps=30)
        try:    
            final__blank_audio = final_blank_video.audio
            self.text_file_instance.track_progress(50)

        except Exception as e:
            logging.error(f"Error loading background music: {e}")
            return
            
        replacement_video_clips=[]
        for video_file in replacement_video_files:
            clip= self.load_video_from_file_field(video_file)
            replacement_video_clips.append(clip)

        logging.info('Done Clipping replacements')

        self.text_file_instance.track_progress(54)
        
        final_video_segments =self.replace_video_segments(output_video_segments, replacement_video_clips, subtitles, blank_vide_clip)
        logging.info('Done  replace_video_segments' )
        concatenated_video = self.concatenate_clips(final_video_segments, target_resolution=MAINRESOLUTIONS[resolution], target_fps=30)
        original_audio = blank_vide_clip.audio.subclip(0, min(concatenated_video.duration, blank_vide_clip.audio.duration))
        final_video = concatenated_video.set_audio(original_audio)  # Removed overwriting with blank audio
        # subtitled_video=self.add_subtitles_from_json(final_video)
        final_video_speeded_up_clip = self.speed_up_video_with_audio(final_video, 1)

        logging.info('generated_final_video successful')
        final_video=self.save_final_video(final_video_speeded_up_clip)
        watermarked= self.add_static_watermark_to_instance(final_video_speeded_up_clip)
        self.text_file_instance.track_progress(100)
            

        self.stdout.write(self.style.SUCCESS(f'Processing complete for {text_file_id}.'))
    
    def save_final_video(self,clip):
        
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_output_video:
            
            self.text_file_instance.track_progress(60)
            
            

            clip.write_videofile(
                temp_output_video.name,
                codec='libx264',
                preset="ultrafast",
                audio_codec="aac",      
                ffmpeg_params=["-movflags", "+faststart"]
            )
            self.text_file_instance.track_progress(70)
            
                # Save the watermarked video to the generated_watermarked_video field
            if self.text_file_instance.generated_final_video:
                self.text_file_instance.generated_final_video.delete(save=False)
                self.text_file_instance.track_progress(74)
        
            with open(temp_output_video.name, 'rb') as output_video_file:
                video_content = output_video_file.read()

                self.text_file_instance.generated_final_video.save(
                    f"final_{self.text_file_instance.id}_{timestamp}.mp4",
                    ContentFile(video_content)
                    )
            self.text_file_instance.track_progress(75)
            return True

    def speed_up_video_with_audio(self,input_video, speed_factor):
        
        sped_up_video = input_video.fx(vfx.speedx, speed_factor)
        
        return sped_up_video

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
                self.text_file_instance.track_progress(5)
            
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
            self.text_file_instance.track_progress(7)


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
            self.text_file_instance.track_progress(8)
            time.sleep(2)
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


    def generate_srt_file(self):
        """
        Download the audio and text files from S3, and process them using a subprocess.
        """
        text_file_instance = self.text_file_instance
        
        # Extract the S3 bucket and file key from the audio and text files
        s3_text_url = text_file_instance.text_file.name  # This gives the S3 key (path within the bucket)
        s3_audio_url = text_file_instance.generated_audio.name  # This gives the S3 key (path within the bucket)

        logging.info(f"Downloading audio from S3: {s3_audio_url}")
        logging.info(f"Downloading text from S3: {s3_text_url}")
        self.text_file_instance.track_progress(12)
        
        # Ensure file paths are not empty
        if not s3_audio_url or not s3_text_url:
            logging.error("Audio or text file path from S3 is empty")
            return False
        
        # Create temporary files to store downloaded audio, text, and SRT files
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_audio, \
            tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_text, \
            tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_srt:
            self.text_file_instance.track_progress(14)

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
            self.text_file_instance.track_progress(16)

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
                self.text_file_instance.track_progress(20)
                
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
                        self.text_file_instance.track_progress(22)

                    # Save the new SRT content to the srt_file field
                    text_file_instance.generated_srt.save(srt_file_name, ContentFile(srt_content))

                    logging.info(f'SRT file saved to instance: {srt_file_name}')
                    time.sleep(3)
                    self.text_file_instance.track_progress(24)

                    return text_file_instance.generated_srt
                
                else:
                    logging.error(f'Error generating SRT file: {result.stderr}')
                    return False
            except Exception as e:
                logging.error(f'An unexpected error occurred while generating the SRT file: {e}')
                return False


    def process_srt_file(self):
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
                
                final_video.write_videofile(temp_output_video.name, fps=24,)

                # Save the final video to the `text_file_instance`
                if text_file_instance.generated_blank_video:
                    text_file_instance.generated_blank_video.delete(save=False)

                # Save the video content correctly
                with open(temp_output_video.name, 'rb') as output_video_file:
                    video_content = output_video_file.read()

                text_file_instance.generated_blank_video.save(f"blank_output_{text_file_instance.id}.mp4", ContentFile(video_content))
                time.sleep(2)
                logging.info(f"Video generated successfully and saved as {text_file_instance.generated_blank_video.name}")
                time.sleep(4)

                return True
            

        except Exception as e:
            logging.error(f"Error generating video: {e}")
            return False

    
    def get_video_duration_from_json(self,json_file):
        with open(json_file, 'r') as file:
            data = json.load(file)

        # Extract the end times from the fragments
        end_times = [fragment['end'] for fragment in data['fragments']]

        # Get the last end time (duration of the video)
        last_end_time = end_times[-1] if end_times else "0.000"

        # Convert the time format (seconds) to float
        return float(last_end_time)


    def load_video_from_instance(self, text_file_instance, file_field) -> VideoFileClip:
        """
        Load a video from the specified file field in the text_file_instance, downloading it from S3,
        and return it as a MoviePy VideoFileClip.

        Args:
            text_file_instance: An instance containing the S3 path for the video file.
            file_field: The name of the file field in text_file_instance that holds the video.

        Returns:
            VideoFileClip: The loaded video clip.

        Raises:
            ValueError: If the specified file field is invalid or not a video file.
        """
        try:
            # Check if the specified file field exists and is valid
            if not hasattr(text_file_instance, file_field):
                raise ValueError(f"{file_field} does not exist in text_file_instance.")
            
            video_file_field = getattr(text_file_instance, file_field)
            
            if not video_file_field or not video_file_field.name:
                raise ValueError(f"Video S3 key is empty for {file_field} in the text_file_instance.")
            
            # Create a temporary file to store the downloaded video
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
                # Download the video file from S3 and save it to the temporary file
                video_content = download_from_s3(video_file_field.name, temp_video.name)
                
                if not video_content:
                    raise ValueError("Failed to download the video from S3.")
                
                # Write the video content to the temp file
                with open(temp_video.name, 'wb') as video_file:
                    video_file.write(video_content)
            
            # Check if the downloaded file is a valid video
            video_clip = VideoFileClip(os.path.normpath(temp_video.name))
            
            # Check for duration or any other validation if needed
            if video_clip.duration <= 0:
                raise ValueError("Downloaded file is not a valid video.")

            # Return the video clip
            return video_clip

        except Exception as e:
            logging.error(f"Error loading video from text_file_instance: {e}")
            raise


    def load_subtitles_from_text_file_instance(self) -> SubRipFile:
        """
        Load subtitles from the generated SRT JSON file in the text_file_instance and convert them to SRT format.

        Returns:
            SubRipFile: The loaded subtitles in SRT format.

        Raises:
            ValueError: If the specified file field is invalid or not a valid JSON file.
        """
        text_file_instance=self.text_file_instance
        try:
            # Check if the specified file field exists and is valid

            json_file_field = text_file_instance.generated_srt

            if not json_file_field or not json_file_field.name:
                raise ValueError(f"JSON S3 key is empty for {json_file_field} in the text_file_instance.")

            # Create a temporary file to store the downloaded JSON
            with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as temp_json:
                # Download the JSON file from S3 and save it to the temporary file
                json_content = download_from_s3(json_file_field.name, temp_json.name)

                if not json_content:
                    raise ValueError("Failed to download the JSON file from S3.")

                # Write the JSON content to the temp file
                with open(temp_json.name, 'wb') as json_file:
                    json_file.write(json_content)

            # Load the JSON data
            with open(temp_json.name, 'r') as file:
                data = json.load(file)

            fragments = data.get('fragments', [])

            # Create a SubRipFile object
            subs = SubRipFile()

            # Iterate through fragments and create SubRipItem for each
            for i, fragment in enumerate(fragments, start=1):
                start_time = self.convert_seconds_to_subrip_time(float(fragment['begin']))
                end_time = self.convert_seconds_to_subrip_time(float(fragment['end']))
                text = "\n".join(fragment['lines'])  # Join the lines to mimic subtitle text
                sub = SubRipItem(index=i, start=start_time, end=end_time, text=text)
                subs.append(sub)
            
            
            return subs

        except Exception as e:
            logging.error(f"Error loading subtitles from text_file_instance: {e}")
            raise
    
    def convert_seconds_to_subrip_time(self,seconds):
        """Helper function to convert seconds into SubRipTime."""
        ms = int((seconds % 1) * 1000)
        s = int(seconds) % 60
        m = (int(seconds) // 60) % 60
        h = (int(seconds) // 3600)
        return SubRipTime(hours=h, minutes=m, seconds=s, milliseconds=ms)

    def subriptime_to_seconds(self,srt_time: pysrt.SubRipTime) -> float:
        return srt_time.hours * 3600 + srt_time.minutes * 60 + srt_time.seconds + srt_time.milliseconds / 1000.0

    def get_segments_using_srt(self,video: VideoFileClip, subtitles: pysrt.SubRipFile) -> (List[VideoFileClip], List[pysrt.SubRipItem]):
        subtitle_segments = []
        video_segments = []
        video_duration = video.duration

        for subtitle in subtitles:
            start = self.subriptime_to_seconds(subtitle.start)
            end = self.subriptime_to_seconds(subtitle.end)

            if start >= video_duration:
                logging.warning(f"Subtitle start time ({start}) is beyond video duration ({video_duration}). Skipping this subtitle.")
                continue

            if end > video_duration:
                logging.warning(f"Subtitle end time ({end}) exceeds video duration ({video_duration}). Clamping to video duration.")
                end = video_duration

            if end <= start:
                logging.warning(f"Invalid subtitle duration: start ({start}) >= end ({end}). Skipping this subtitle.")
                continue

            video_segment = video.subclip(start, end)
            if video_segment.duration == 0:
                logging.warning(f"Video segment duration is zero for subtitle ({subtitle.text}). Skipping this segment.")
                continue

            subtitle_segments.append(subtitle)
            video_segments.append(video_segment)

        return video_segments, subtitle_segments


    def adjust_segment_duration(self,segment: VideoFileClip, duration: float) -> VideoFileClip:
        current_duration = segment.duration
        if current_duration < duration:
            return loop(segment, duration=duration)
        elif current_duration > duration:
            return segment.subclip(0, duration)
        return segment

    def get_video_paths_for_text_file(self):
        """
        Get a list of video paths for all TextLineVideoClip instances associated with the given text_file_instance.
        
        Args:
            text_file_instance: An instance of the TextFile model.

        Returns:
            List[str]: A list of video paths.
        """
        video_clips = TextLineVideoClip.objects.filter(text_file=self.text_file_instance)
        return [clip.to_dict().get("video_path") for clip in video_clips]


    def load_video_from_file_field(self,file_field) -> VideoFileClip:
        """
        Load a video from a file field, downloading it from S3,
        and return it as a MoviePy VideoFileClip.

        Args:
            file_field: The FileField containing the S3 path for the video file.

        Returns:
            VideoFileClip: The loaded video clip.

        Raises:
            ValueError: If the file field is empty or not a valid video file.
        """
        try:
            # Ensure that the file field is valid
            if not file_field or not file_field.name:
                raise ValueError("File field is empty or invalid.")

            # Create a temporary file to store the downloaded video
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
                # Download the video file from S3 and save it to the temporary file
                video_content = download_from_s3(file_field.name, temp_video.name)

                if not video_content:
                    raise ValueError("Failed to download the video from S3.")

                # Write the video content to the temp file
                with open(temp_video.name, 'wb') as video_file:
                    video_file.write(video_content)

                # Load the video using MoviePy
                video_clip = VideoFileClip(os.path.normpath(temp_video.name))

                # Return the video clip
                return video_clip

        except Exception as e:
            logging.error(f"Error loading video from file field: {e}")
            raise




    # def load_video_from_file_field(self, file_field) -> VideoFileClip:
    #     """
    #     Load a video from a file field, downloading it from S3,
    #     convert it using ffmpeg if necessary, and return it as a MoviePy VideoFileClip.

    #     Args:
    #         file_field: The FileField containing the S3 path for the video file.

    #     Returns:
    #         VideoFileClip: The loaded video clip.

    #     Raises:
    #         ValueError: If the file field is empty or not a valid video file.
    #     """
    #     try:
    #         # Ensure that the file field is valid
    #         if not file_field or not file_field.name:
    #             raise ValueError("File field is empty or invalid.")

    #         # Create a temporary file to store the downloaded video
    #         with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_video:
    #             # Download the video file from S3 and save it to the temporary file
    #             video_content = download_from_s3(file_field.name, temp_video.name)

    #             if not video_content:
    #                 raise ValueError("Failed to download the video from S3.")

    #             # Write the video content to the temp file
    #             with open(temp_video.name, 'wb') as video_file:
    #                 video_file.write(video_content)

    #             # Create another temporary file for the converted video
    #             with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as converted_video:
    #                 converted_video_path = os.path.normpath(converted_video.name)

    #                 # Use ffmpeg to convert the video
    #                 input_video_path = os.path.normpath(temp_video.name)
    #                 ffmpeg_command = [
    #                     'ffmpeg',
    #                     '-y',
    #                     '-i', input_video_path,
    #                     '-c:v', 'libx264',
    #                     '-c:a', 'aac',
    #                     converted_video_path
    #                 ]

    #                 # Run the ffmpeg command
    #                 subprocess.run(ffmpeg_command, check=True)

    #                 # Load the converted video using MoviePy
    #                 video_clip = VideoFileClip(converted_video_path)

    #                 # Return the video clip
    #                 logging.info('Clip loaded!')
    #                 return video_clip

    #     except subprocess.CalledProcessError as ffmpeg_error:
    #         logging.error(f"FFmpeg error: {ffmpeg_error}")
    #         raise ValueError("Video conversion failed using FFmpeg.")
    #     except Exception as e:
    #         logging.error(f"Error loading video from file field: {e}")


    def crop_to_aspect_ratio_(self,clip, desired_aspect_ratio):
        # Get the original clip dimensions
        original_width, original_height = clip.size
        
        # Calculate the current aspect ratio
        original_aspect_ratio = original_width / original_height
        
        # If the aspect ratio is already correct, return the original clip
        if abs(original_aspect_ratio - desired_aspect_ratio) < 0.01:  # Allow small rounding errors
            return clip
        
        # Calculate the new width and height to match the desired aspect ratio
        if original_aspect_ratio > desired_aspect_ratio:
            # The clip is too wide, we need to reduce the width
            new_width = int(original_height * desired_aspect_ratio)
            new_height = original_height
            x1 = (original_width - new_width) // 2  # Center the crop horizontally
            y1 = 0
        else:
            # The clip is too tall, we need to reduce the height
            new_width = original_width
            new_height = int(original_width / desired_aspect_ratio)
            x1 = 0
            y1 = (original_height - new_height) // 2  # Center the crop vertically
        
        x2 = x1 + new_width
        y2 = y1 + new_height
        
        # Crop the clip to the new dimensions
        return crop(clip, x1=x1, y1=y1, x2=x2, y2=y2)




    def concatenate_clips(self,clips, target_resolution=None, target_fps=None):
        """
        Concatenates a list of VideoFileClip objects into a single video clip.

        Args:
            clips (list): List of VideoFileClip objects to concatenate.
            target_resolution (tuple, optional): Target resolution (width, height) to resize videos. Defaults to None.
            target_fps (int, optional): Target frames per second to unify videos. Defaults to None.

        Returns:
            VideoFileClip: The concatenated video clip.
        """
        # Prepare a list to store modified clips
        processed_clips = []

        for clip in clips:
            clip =self.crop_to_aspect_ratio_(clip,target_resolution)
            if target_fps:
                
                clip = clip.set_fps(target_fps)  # Set frame rate to target fps
            processed_clips.append(clip)
        resized_clips=self.resize_clips_to_max_size(processed_clips)
        # Concatenate all video clips
        final_clip = concatenate_videoclips(resized_clips, method="compose")
        logging.info('Clip has been concatenated: ')
        return final_clip


    def resize_clips_to_max_size(self,clips):
        # Step 1: Get the maximum width and height from the clips
        max_width = max(clip.w for clip in clips)
        max_height = max(clip.h for clip in clips)

        # Step 2: Resize each clip to the maximum width and height
        resized_clips = [clip.resize(newsize=(max_width, max_height)) for clip in clips]

        return resized_clips



    def replace_video_segments(self,
        original_segments: List[VideoFileClip],
        replacement_videos: Dict[int, VideoFileClip],
        subtitles: pysrt.SubRipFile,
        original_video: VideoFileClip,
        
        
    ) -> List[VideoFileClip]:
        combined_segments = original_segments.copy()
        for replace_index in range(len(replacement_videos)):
            if 0 <= replace_index < len(combined_segments):
                target_duration = combined_segments[replace_index].duration
                start = self.subriptime_to_seconds(subtitles[replace_index].start)
                end = self.subriptime_to_seconds(subtitles[replace_index].end)

                # Adjust replacement video duration to match target duration

                if replacement_videos[replace_index].duration < target_duration:
                    replacement_segment = loop(replacement_videos[replace_index], duration=target_duration)
                else:
                    replacement_segment = replacement_videos[replace_index].subclip(0, target_duration)

                adjusted_segment = self.adjust_segment_properties(replacement_segment, original_video,)
                adjusted_segment_with_subtitles = self.add_subtitles_to_clip(adjusted_segment, subtitles[replace_index])
                combined_segments[replace_index] = adjusted_segment_with_subtitles
        print('combined_segments combined_segments combined_segments combined_segments ', combined_segments)
        return combined_segments

    def adjust_segment_properties(self,segment: VideoFileClip, original: VideoFileClip) -> VideoFileClip:
        segment = segment.set_fps(original.fps)
        segment = segment.set_duration(segment.duration)
        return segment


    def add_subtitles_to_clip(self ,clip: VideoFileClip, subtitle: pysrt.SubRipItem) -> VideoFileClip:
        logging.info(f"Adding subtitle: {subtitle.text}")
        subtitle_box_color=self.text_file_instance.subtitle_box_color
        base_font_size=self.text_file_instance.font_size-3
        color=self.text_file_instance.font_color
        margin=29
        font_path=self.text_file_instance.font
        if margin is None:
            # Set default margin or handle the case when margin is None
            margin = 30
        x,y,z =mcolors.to_rgb(subtitle_box_color)
        subtitle_box_color=(x*255,y*255,z*255)
        
        # Calculate the scaling factor based on the resolution of the clip
        scaling_factor = (clip.h / 1080)
        font_size = int(int(base_font_size) * scaling_factor)
        font_path_=fonts.get(font_path,'Montserrat')

        def split_text(text: str, max_line_width: int) -> str:
            words = text.split()
            lines = []
            current_line = []
            current_length = 0

            for word in words:
                if current_length + len(word) <= max_line_width:
                    current_line.append(word)
                    current_length += len(word) + 1  # +1 for the space
                else:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_length = len(word) + 1

            if current_line:
                lines.append(" ".join(current_line))

            return "\n".join(lines)

        # Function to ensure the subtitle text does not exceed two lines
        def ensure_two_lines(text: str, initial_max_line_width: int, initial_font_size: int) -> (str, int):
            max_line_width = initial_max_line_width
            font_size = initial_font_size
            wrapped_text = split_text(text, max_line_width)

            # Adjust until the text fits in two lines
            while wrapped_text.count('\n') > 1:
                max_line_width += 1
                font_size -= 1
                wrapped_text = split_text(text, max_line_width)

                # Stop adjusting if font size becomes too small
                if font_size < 20:
                    break

            return wrapped_text, font_size

        max_line_width = 35  # Initial value, can be adjusted

        if len(subtitle.text) > 60:
            wrapped_text, adjusted_font_size = ensure_two_lines(subtitle.text, max_line_width, font_size)
        else:
            wrapped_text, adjusted_font_size = split_text(subtitle.text, max_line_width), font_size

        # Create a temporary TextClip to measure the width of the longest line

        
        temp_subtitle_clip = TextClip(
            wrapped_text,
            fontsize=font_size,
            font=font_path_,
        )
        longest_line_width, text_height = temp_subtitle_clip.size
        
        subtitle_clip = TextClip(
            wrapped_text,
            fontsize=adjusted_font_size,
            color=color,
            # stroke_color="white",
            stroke_width=0,
            font=font_path_,
            method='caption',
            align='center',
            size=(longest_line_width, None)  # Use the measured width for the longest line
        ).set_duration(clip.duration)

        text_width, text_height = subtitle_clip.size
        small_margin = 8  # Small margin for box width
        box_width = text_width + small_margin  # Adjust the box width to be slightly larger than the text width
        box_height = text_height + margin
        box_clip = ColorClip(size=(box_width, box_height), color=subtitle_box_color).set_opacity(0.7).set_duration(subtitle_clip.duration)
        print('this is the used box color:',subtitle_box_color )
        # Adjust box position to be slightly higher in the video
        box_position = ('center', clip.h - box_height - 2 * margin)
        subtitle_position = ('center', clip.h - box_height - 2 * margin + (box_height - text_height) / 2)

        box_clip = box_clip.set_position(box_position)
        subtitle_clip = subtitle_clip.set_position(subtitle_position)

        return CompositeVideoClip([clip, box_clip, subtitle_clip])
        # return clip


    def add_animated_watermark_to_instance(self, video):
        """
        Add an animated watermark to the video from text_file_instance and save the result.
        """
        watermark_s3_path=LogoModel.objects.first().logo.name

        text_file_instance = self.text_file_instance

        # Define the path where the logo will be temporarily stored
        # logo_path = os.path.join(os.getcwd(),'media','vlc','logo.png')
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as watermark_temp_path:

            content=download_from_s3(watermark_s3_path, watermark_temp_path.name) 
            self.text_file_instance.track_progress(78)

            with open(watermark_temp_path.name, 'wb') as png_file:
                    png_file.write(content)   
            try:
                watermark = ImageClip(watermark_temp_path.name).resize(width=video.w * 0.6).set_opacity(0.5)
                self.text_file_instance.track_progress(79)

            except Exception as e:
                logging.error(f"Error loading watermark image: {e}")
                return False

            # Function to calculate the new position of the watermark
            def moving_watermark(t):
                speed_x, speed_y = 300, 280
                pos_x = np.abs((speed_x * t) % (2 * video.w) - video.w)
                pos_y = np.abs((speed_y * t) % (2 * video.h) - video.h)
                return (pos_x, pos_y)

            # Animate the watermark
            watermark = watermark.set_position(moving_watermark, relative=False).set_duration(video.duration)
            self.text_file_instance.track_progress(82)

            # Overlay the animated watermark on the video
            watermarked = CompositeVideoClip([video, watermark], size=video.size)
            watermarked.set_duration(video.duration)
            self.text_file_instance.track_progress(83)

            # Save the output to a temporary file
            try:
                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_output_video:
                    watermarked.write_videofile(
                        temp_output_video.name,
                        codec='libx264',
                        preset="ultrafast",
                        audio_codec="aac",      
                        ffmpeg_params=["-movflags", "+faststart"]
                    )
                    self.text_file_instance.track_progress(94)

                    # Save the watermarked video to the model field
                    if text_file_instance.generated_watermarked_video:
                        text_file_instance.generated_watermarked_video.delete(save=False)
                        self.text_file_instance.track_progress(97)

                    with open(temp_output_video.name, 'rb') as temp_file:
                        text_file_instance.generated_watermarked_video.save(
                            f"watermarked_output_{text_file_instance.id}.mp4",
                            ContentFile(temp_file.read())
                        )
                        self.text_file_instance.track_progress(99)


                logging.info("Watermarked video generated successfully.")
                return True

            except Exception as e:
                logging.error(f"Error generating watermarked video: {e}")
                return False
    
    def add_static_watermark_to_instance(self, video):
        """
        Add a static watermark to the video from text_file_instance and save the result.
        """
        text_file_instance = self.text_file_instance

        # Get the watermark from the S3 path
        watermark_s3_path = LogoModel.objects.first().logo.name

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as watermark_temp_path:
            content = download_from_s3(watermark_s3_path, watermark_temp_path.name)
            with open(watermark_temp_path.name, 'wb') as png_file:
                png_file.write(content)
        
        try:
            # Load the watermark image and resize it to 80% of the video width
            watermark = ImageClip(watermark_temp_path.name).resize(width=video.w * 1).set_opacity(0.7)
        except Exception as e:
            logging.error(f"Error loading watermark image: {e}")
            return False

        # Position the watermark in the center of the video
        watermark = watermark.set_position(("center", "center")).set_duration(video.duration)

        # Overlay the static watermark on the video
        watermarked = CompositeVideoClip([video, watermark], size=video.size)
        watermarked.set_duration(video.duration)
        self.text_file_instance.track_progress(88)

        # Save the output to a temporary file
        try:
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_output_video:
                watermarked.write_videofile(
                    temp_output_video.name,
                    codec='libx264',
                    preset="ultrafast",
                    audio_codec="aac",
                    ffmpeg_params=["-movflags", "+faststart"]
                )
                self.text_file_instance.track_progress(95)

                
                # Save the watermarked video to the model field
                if text_file_instance.generated_watermarked_video:
                    text_file_instance.generated_watermarked_video.delete(save=False)
                    self.text_file_instance.track_progress(97)

                with open(temp_output_video.name, 'rb') as temp_file:
                    text_file_instance.generated_watermarked_video.save(
                        f"watermarked_output_{text_file_instance.id}.mp4",
                        ContentFile(temp_file.read())
                    )
                    self.text_file_instance.track_progress(99)

            logging.info("Watermarked video generated successfully.")
            time.sleep(5)

            self.text_file_instance.track_progress(100)

            return True

        except Exception as e:
            logging.error(f"Error generating watermarked video: {e}")
            return False

  

    def add_subtitles_from_json(self, clip: VideoFileClip) -> VideoFileClip:
        text_file_instance=self.text_file_instance
        font_path=self.text_file_instance.font

        try:
            # Read JSON content from the text_file_instance
            with text_file_instance.generated_srt.open('r') as json_file:
                srt_json_content = json_file.read()
            
            # Parse the JSON content
            subtitle_json = json.loads(srt_json_content)

        except json.JSONDecodeError as e:
            raise Exception(f"JSON parsing error: {e}")
        except Exception as e:
            raise Exception(f"Error accessing the JSON file: {e}")

        subtitle_clips = []
        subtitle_box_color = text_file_instance.subtitle_box_color
        base_font_size = text_file_instance.font_size
        color = text_file_instance.font_color
        margin = 29
        scaling_factor = (clip.h / 1080)  # Adjust font size based on resolution
        font_size = int(base_font_size * scaling_factor)

        def split_text(text: str, max_line_width: int) -> str:
            words = text.split()
            lines = []
            current_line = []
            current_length = 0

            for word in words:
                if current_length + len(word) <= max_line_width:
                    current_line.append(word)
                    current_length += len(word) + 1
                else:
                    lines.append(" ".join(current_line))
                    current_line = [word]
                    current_length = len(word) + 1

            if current_line:
                lines.append(" ".join(current_line))

            return "\n".join(lines)

        def ensure_two_lines(text: str, initial_max_line_width: int, initial_font_size: int) -> (str, int):
            max_line_width = initial_max_line_width
            font_size = initial_font_size
            wrapped_text = split_text(text, max_line_width)

            while wrapped_text.count('\n') > 1:
                max_line_width += 1
                font_size -= 1
                wrapped_text = split_text(text, max_line_width)

                if font_size < 20:
                    break

            return wrapped_text, font_size

        max_line_width = 35  # Initial value, can be adjusted

        for fragment in subtitle_json['fragments']:
            start_time = float(fragment['begin'])
            end_time = float(fragment['end'])
            subtitle_text = "\n".join(fragment['lines'])
            subtitle_box_color=self.text_file_instance.subtitle_box_color
            if len(subtitle_text) > 60:
                wrapped_text, adjusted_font_size = ensure_two_lines(subtitle_text, max_line_width, font_size)
            else:
                wrapped_text, adjusted_font_size = split_text(subtitle_text, max_line_width), font_size

            temp_subtitle_clip = TextClip(
                wrapped_text,
                fontsize=adjusted_font_size,
                font=fonts.get(font_path,'Georgia-Bold')
            )
            longest_line_width, text_height = temp_subtitle_clip.size
            ne_text=soft_wrap_text(
                    wrapped_text,

                    font_family=fonts.get(font_path,'Georgia-Bold'),
                    fontsize=font_size,
                    letter_spacing=12,
                    max_width=clip.w * .8  # *0.8 for some padding
                )
            subtitle_clip = TextClip(
                ne_text,
                fontsize=adjusted_font_size,
                color=color,
                stroke_width=0,
                bg_color=subtitle_box_color,
                font=os.path.join(os.getcwd(),'fonts','31692f02-5637-4cd2-b973-99a09e542b83.ttf'),
                method='caption',
                align='center',
                # kerning=12,
                size=(longest_line_width, None)
            ).set_duration(end_time - start_time)
            
            x, y, z = mcolors.to_rgb(subtitle_box_color)
            subtitle_box_color = (x * 255, y * 255, z * 255)  # Convert to RGB


            small_margin = 8
            box_width = longest_line_width + small_margin
            box_height = text_height + margin
            box_clip = ColorClip(size=(box_width, box_height), color=subtitle_box_color).set_opacity(0.7).set_duration(subtitle_clip.duration)

            box_position = ('center', clip.h - box_height - 2 * margin)
            subtitle_position = ('center', clip.h - box_height - 2 * margin + (box_height - text_height) / 2)

            box_clip = box_clip.set_position(box_position)
            subtitle_clip = subtitle_clip.set_position(subtitle_position)

            subtitle_clips.append(subtitle_clip.set_start(start_time))

        final_clip = CompositeVideoClip([clip] + subtitle_clips)
        return final_clip

def soft_wrap_text(
    text: str, 
    fontsize: int, 
    letter_spacing: int, 
    font_family: str, 
    max_width: int,
):
    # Note that font_family has to be an absolut path to your .ttf/.otf
    image_font = ImageFont.truetype(font_family, fontsize) 

    # I am not sure my letter spacing calculation is accurate
    text_width = image_font.getlength(text) + (len(text)-1) * letter_spacing 
    letter_width = text_width / len(text)

    if text_width < max_width:
        return text

    max_chars = max_width / letter_width
    wrapped_text = textwrap.fill(text, width=max_chars)
    return wrapped_text


def add_animated_watermark(text_file_instance):
    # Create temporary paths for downloaded files
    video_temp_path = tempfile.mktemp(suffix=".mp4")
    video_s3_path=text_file_instance.generated_final_video.name
    # Download video and watermark from S3
    watermark_temp_path = tempfile.mktemp(suffix=".png")
    watermark_s3_path=LogoModel.objects.first().logo.name
    download_from_s3(watermark_s3_path, watermark_temp_path)
    download_from_s3(video_s3_path, video_temp_path)

    # Load the video
    cap = cv2.VideoCapture(video_temp_path)
    
    if not cap.isOpened():
        logging.error(f"Error opening video file: {video_temp_path}")
        return

    # Get video properties
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Load the watermark
    watermark = cv2.imread(watermark_temp_path, cv2.IMREAD_UNCHANGED)
    if watermark is None:
        logging.error(f"Error loading watermark image: {watermark_temp_path}")
        return

    watermark = cv2.resize(watermark, (int(width * 0.6), int(height * 0.6)))  # Resize watermark
    watermark_height, watermark_width = watermark.shape[:2]

    # Create VideoWriter to save the output
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec
    output_temp_path = tempfile.mktemp(suffix=".mp4")  # Temporary output path
    out = cv2.VideoWriter(output_temp_path, fourcc, fps, (width, height))

    # Position variables
    pos_x, pos_y = 0, 0
    speed_x, speed_y = 5, 3  # Speed of the watermark

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Draw the watermark on the frame
        frame[pos_y:pos_y + watermark_height, pos_x:pos_x + watermark_width] = watermark

        # Update watermark position
        pos_x += speed_x
        pos_y += speed_y

        # Bounce the watermark off the edges
        if pos_x + watermark_width > width or pos_x < 0:
            speed_x = -speed_x
        if pos_y + watermark_height > height or pos_y < 0:
            speed_y = -speed_y

        # Write the frame with the watermark
        out.write(frame)

    # Release resources
    cap.release()
    out.release()
    cv2.destroyAllWindows()

    # Save the output video to the model field
    with open(output_temp_path, 'rb') as temp_file:
        text_file_instance.generated_watermarked_video.save(
            f"watermarked_output_{text_file_instance.id}.mp4",
            ContentFile(temp_file.read())
        )

    # Clean up temporary files
    os.remove(video_temp_path)
    os.remove(watermark_temp_path)
    os.remove(output_temp_path)

    logging.info("Watermarked video generated successfully and saved to the model.")


