
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

def parse_srt_to_json(srt_file_path: str) -> Dict:
    """
    Parses an SRT file and converts it into a JSON structure.

    Args:
        srt_file_path (str): Path to the SRT file.

    Returns:
        Dict: JSON structure with subtitle fragments.
    """
    def parse_time(time_str: str) -> str:
        """Convert SRT time format to seconds."""
        hours, minutes, seconds = map(float, re.split('[:,]', time_str))
        return f"{hours * 3600 + minutes * 60 + seconds:.3f}"

    fragments = []
    with open(srt_file_path, 'r') as srt_file:
        content = srt_file.read()

        # Split content by double new lines
        blocks = content.strip().split('\n\n')
        for block in blocks:
            lines = block.split('\n')
            if len(lines) < 3:
                continue
            
            # Extract time range
            time_range = lines[1]
            begin_time, end_time = time_range.split(' --> ')
            begin = parse_time(begin_time.strip())
            end = parse_time(end_time.strip())

            # Extract text lines
            text_lines = [line.strip() for line in lines[2:] if line.strip()]
            
            # Create fragment dictionary
            fragment = {
                "begin": begin,
                "end": end,
                "id": f"f{str(len(fragments)+1).zfill(6)}",
                "language": "eng",
                "lines": text_lines
            }
            fragments.append(fragment)
    
    # Return JSON structure
    return {"fragments": fragments}


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


def generate_srt_file(audio_file_path, text_file_path, output_srt_file_path):
    """
    Generates an SRT file using Aeneas from the provided text and audio file paths.
    """
    # Aeneas command to generate SRT
    os.makedirs(os.path.dirname(output_srt_file_path), exist_ok=True)
    command = f'python3.10 -m aeneas.tools.execute_task "{audio_file_path}" "{text_file_path}" ' \
              f'"task_language=eng|is_text_type=plain|os_task_file_format=json" "{output_srt_file_path}"'

    try:
        # Run the command using subprocess
        logging.info(f'Running command: {command}')
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Log command output
        logging.info(f'Command output: {result.stdout}')

        # Check for errors in subprocess execution
        if result.returncode == 0:
            logging.info(f'SRT file generated successfully: {output_srt_file_path}')
            return output_srt_file_path  # Return the path of the generated SRT file
        else:
            logging.error(f'Error generating SRT file: {result.stderr}')
            return None
    except Exception as e:
        logging.error(f'An unexpected error occurred while generating SRT file: {e}')
        return None

def convert_text_to_speech(text_file_path, voice_id, api_key, output_audio_file='audio_files/output.mp3'):
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
        with open(text_file_path, "r") as text_file:
            text = text_file.read().strip()
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


def crop_to_aspect_ratio(clip, target_resolution):
    # Get the current video width and height
    video_width, video_height = clip.size
    target_width, target_height = target_resolution

    # Calculate aspect ratios
    video_aspect_ratio = video_width / video_height
    target_aspect_ratio = target_width / target_height

    # Check if the aspect ratios match
    if video_aspect_ratio == target_aspect_ratio:
        # If the aspect ratio matches, return the original clip
        return clip
    else:
        # Crop the video to the target resolution, centering the crop on the video
        if video_aspect_ratio > target_aspect_ratio:
            # Video is wider than the target, so crop width
            new_width = int(target_aspect_ratio * video_height)
            cropped_clip = crop(clip, width=new_width, height=video_height,
                                x_center=video_width / 2, y_center=video_height / 2)
        else:
            # Video is taller than the target, so crop height
            new_height = int(video_width / target_aspect_ratio)
            cropped_clip = crop(clip, width=video_width, height=new_height,
                                x_center=video_width / 2, y_center=video_height / 2)

        return cropped_clip
from moviepy.editor import VideoFileClip, ColorClip, CompositeVideoClip

def resize_to_aspect_ratio(videoclip, target_resolution):
    # Get video dimensions
    video_width, video_height = videoclip.size
    target_width, target_height = target_resolution

    # Calculate aspect ratios
    video_aspect_ratio = video_width / video_height
    target_aspect_ratio = target_width / target_height

    # If the aspect ratio of the target matches the video, and the resolution is not larger, return the original video
    if target_aspect_ratio == video_aspect_ratio and target_width <= video_width and target_height <= video_height:
        return videoclip

    # Otherwise, we need to embed the video in a background
    # Maintain aspect ratio and determine whether padding is needed on width or height

    if target_aspect_ratio > video_aspect_ratio:
        # The target is wider relative to its height than the video
        # We will need padding on the left and right
        new_video_height = target_height
        new_video_width = int(new_video_height * video_aspect_ratio)
    else:
        # The target is taller relative to its width than the video
        # We will need padding on the top and bottom
        new_video_width = target_width
        new_video_height = int(new_video_width / video_aspect_ratio)

    # Resize the video to the new dimensions (preserving aspect ratio)
    resized_video = videoclip.resize((new_video_width, new_video_height))

    # Calculate position to center the resized video
    x_pos = (target_width - new_video_width) // 2
    y_pos = (target_height - new_video_height) // 2

    # Create a background
    background = ColorClip(size=target_resolution, color=(0, 0, 0), duration=videoclip.duration)

    # Position the resized video on top of the background
    final_clip = CompositeVideoClip([background, resized_video.set_position((x_pos, y_pos))])

    return final_clip


# def resize_to_aspect_ratio(videoclip, target_resolution):
#     background = ColorClip(color=(0, 0, 0), size=target_resolution, duration=videoclip.duration)
    
#     # Calculate position to center the video within the target resolution
#     video_width, video_height = videoclip.size
#     target_width, target_height = target_resolution
#     x_pos = (target_width - video_width) // 2
#     y_pos = (target_height - video_height) // 2
    
#     # Position the video on top of the background
#     final_clip = CompositeVideoClip([background, videoclip.set_position((x_pos, y_pos))])
    
#     return final_clip


# def resize_to_aspect_ratio(video: VideoFileClip, desired_aspect_ratio: float) -> VideoFileClip:
#     """
#     Resize the video while maintaining its original aspect ratio to fit within the desired aspect ratio.

#     Args:
#         video (VideoFileClip): The original video clip.
#         desired_aspect_ratio (float): The desired aspect ratio (width/height).

#     Returns:
#         VideoFileClip: The resized video clip.
#     """
#     # Calculate the current aspect ratio of the video
#     video_aspect_ratio = video.w / video.h

#     # Determine how to scale the video based on the desired aspect ratio
#     if video_aspect_ratio > desired_aspect_ratio:
#         # Video is wider than desired aspect ratio, fit to width
#         new_width = video.w
#         new_height = int(video.w / desired_aspect_ratio)
#     else:
#         # Video is taller than desired aspect ratio, fit to height
#         new_width = int(video.h * desired_aspect_ratio)
#         new_height = video.h

#     # Resize the video to the new dimensions while preserving the original aspect ratio
#     resized_video = video.resize(newsize=(new_width, new_height))

#     return resized_video

def embed_in_background(video: VideoFileClip, target_resolution: tuple) -> VideoFileClip:
    """
    Embed a video in a black background of the target resolution.

    Args:
        video (VideoFileClip): The input video clip.
        target_resolution (tuple): The target resolution (width, height) to fit the video into.

    Returns:
        VideoFileClip: A new video clip with the original video centered on a black background.
    """
    # Target resolution and aspect ratio
    target_width, target_height = target_resolution
    target_aspect_ratio = target_width / target_height

    # Original video aspect ratio
    video_aspect_ratio = video.w / video.h

    # Determine the size of the background
    if video_aspect_ratio > target_aspect_ratio:
        # The video is wider than the target aspect ratio
        new_width = target_width
        new_height = int(target_width / video_aspect_ratio)
    else:
        # The video is taller than the target aspect ratio
        new_width = int(target_height * video_aspect_ratio)
        new_height = target_height

    # Create a black background clip with the target resolution
    background = ColorClip(size=(target_width, target_height), color=(0, 0, 0))

    # Resize the video to fit within the target resolution, maintaining aspect ratio
    resized_video = video.resize(newsize=(new_width, new_height))

    # Calculate position to center the resized video
    x_center = (target_width - new_width) // 2
    y_center = (target_height - new_height) // 2

    # Overlay the resized video on the black background
    final_clip = CompositeVideoClip([background, resized_video.set_position((x_center, y_center))])
    final_clip.write_videofile(os.path.join(os.getcwd(),'cropped','video.mp4'), codec='libx264', audio_codec='aac')

    return final_clip



def load_subtitles_from_txt_file(srt_file: Path) -> pysrt.SubRipFile:
    # if not srt_file.exists():
    #     raise FileNotFoundError(f"SRT File not found: {srt_file}")
    return pysrt.open(srt_file)

# Predefined resolutions
RESOLUTIONS = {
    '1:1': (480, 480),
    '16:9': (1920, 1080),
    '4:5': (800, 1000),
    '9:16': (1080, 1920)
}

def update_progress(progress,dir_s):
    with open(dir_s, 'w') as f:
        f.write(str(progress))


def get_video_duration_from_srt(srt_file):
    with open(srt_file, 'r') as file:
        content = file.read()
    timestamps = re.findall(r'\d{2}:\d{2}:\d{2},\d{3}', content)
    end_times = timestamps[1::2]  # Get all end times
    last_end_time = end_times[-1] if end_times else "00:00:00,000"
    h, m, s_ms = last_end_time.split(':')
    s, ms = s_ms.split(',')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def get_video_duration_from_json(json_file):
    with open(json_file, 'r') as file:
        data = json.load(file)

    # Extract the end times from the fragments
    end_times = [fragment['end'] for fragment in data['fragments']]

    # Get the last end time (duration of the video)
    last_end_time = end_times[-1] if end_times else "0.000"

    # Convert the time format (seconds) to float
    return float(last_end_time)

# Example usage

def generate_blank_video_with_audio(audio_file, srt_file, output_file, resolution='16:9'):
    # Get the duration from the SRT file
    srt_duration = get_video_duration_from_json(srt_file)

    # Get the duration of the audio file
    audio_clip = AudioFileClip(audio_file)
    audio_duration = audio_clip.duration

    # Determine the maximum duration between the SRT and audio file
    duration = max(srt_duration, audio_duration)

    # Get the resolution size from the dictionary
    if resolution in RESOLUTIONS:
        width, height = RESOLUTIONS[resolution]
    else:
        raise ValueError(f"Resolution '{resolution}' is not supported. Choose from {list(RESOLUTIONS.keys())}.")

    # Create a blank (black) clip with the specified aspect ratio
    blank_clip = ColorClip(size=(width, height), color=(0, 0, 0)).set_duration(duration)

    # Combine the audio with the blank video
    final_video = CompositeVideoClip([blank_clip]).set_audio(audio_clip)

    # Write the final video to a file
    final_video.write_videofile(output_file, fps=24)
    return final_video

def get_segments_using_srt_file(srt_file: Path) -> int:
    subtitles = load_subtitles_from_txt_file(srt_file)
    return len(subtitles)


def load_video_from_file(file: Path) -> VideoFileClip:
    # if not file.exists():
    #     raise FileNotFoundError(f"Video file not found: {file}")
    return VideoFileClip(os.path.normpath(file))


# Define a class that mimics the structure of SubRipItem
class SubtitleItem:
    def __init__(self, index, start, end, text):
        self.index = index
        self.start = start
        self.end = end
        self.text = text

    def __repr__(self):
        return f"SubtitleItem({self.index}, start={self.start}, end={self.end}, text='{self.text}')"



def convert_seconds_to_subrip_time(seconds):
    """Helper function to convert seconds into SubRipTime."""
    ms = int((seconds % 1) * 1000)
    s = int(seconds) % 60
    m = (int(seconds) // 60) % 60
    h = (int(seconds) // 3600)
    return SubRipTime(hours=h, minutes=m, seconds=s, milliseconds=ms)


def speed_up_video_with_audio(input_video, output_video_path, speed_factor):
    # Speed up the video and audio using speedx
    sped_up_video = input_video.fx(vfx.speedx, speed_factor)

    # Write the sped-up video to the output path
    # sped_up_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')

    # Return the sped-up video as a VideoClip object
    return sped_up_video


def load_subtitles_from_json_to_srt(json_file_path):
    # Load the JSON data
    with open(json_file_path, 'r') as file:
        data = json.load(file)

    fragments = data.get('fragments', [])

    # Create a SubRipFile object
    subs = SubRipFile()

    # Iterate through fragments and create SubRipItem for each
    for i, fragment in enumerate(fragments, start=1):
        start_time = convert_seconds_to_subrip_time(float(fragment['begin']))
        end_time = convert_seconds_to_subrip_time(float(fragment['end']))
        text = "\n".join(fragment['lines'])  # Join the lines to mimic subtitle text
        sub = SubRipItem(index=i, start=start_time, end=end_time, text=text)
        subs.append(sub)

    return subs


def subriptime_to_seconds(srt_time: pysrt.SubRipTime) -> float:
    return srt_time.hours * 3600 + srt_time.minutes * 60 + srt_time.seconds + srt_time.milliseconds / 1000.0

def get_segments_using_srt(video: VideoFileClip, subtitles: pysrt.SubRipFile) -> (List[VideoFileClip], List[pysrt.SubRipItem]):
    subtitle_segments = []
    video_segments = []
    video_duration = video.duration

    for subtitle in subtitles:
        start = subriptime_to_seconds(subtitle.start)
        end = subriptime_to_seconds(subtitle.end)

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


def adjust_segment_duration(segment: VideoFileClip, duration: float) -> VideoFileClip:
    current_duration = segment.duration
    if current_duration < duration:
        return loop(segment, duration=duration)
    elif current_duration > duration:
        return segment.subclip(0, duration)
    return segment
def extract_video_paths(json_file_path):
    # Load the JSON file
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    
    # Extract video paths into a list
    video_paths = [clip['video_path'] for clip in data]
    
    return video_paths

def add_subtitles_to_clip(subtitle_box_color ,clip: VideoFileClip, subtitle: pysrt.SubRipItem, base_font_size: int = 42, color: str = "white", margin: int = 30,font_path: str = os.path.join(os.getcwd(), 'data', "Montserrat-SemiBold.ttf")) -> VideoFileClip:
    logging.info(f"Adding subtitle: {subtitle.text}")
    if margin is None:
        # Set default margin or handle the case when margin is None
        margin = 20
        print('PR7 subtitle_box_color: ',subtitle_box_color)
    if subtitle_box_color is None:
        subtitle_box_color = (1, .3, .5)
    elif subtitle_box_color:
        # Your string

        # Step 1: Strip the parentheses and whitespace
        subtitle_box_color = subtitle_box_color.strip(' ()')

        print(' Step 2: Split the string by commas')
        values = subtitle_box_color.split(',')

        # Step 3: Convert the split values to floats
        x, y, z = map(float, values)

        # Now x, y, z hold the values 0.9, 0.7, 0.4

        subtitle_box_color=(x,y,z)
    # font_path = os.path.join(os.getcwd(), 'data', "Montserrat-SemiBold.ttf") # Update this path to where the font file is located

    # Calculate the scaling factor based on the resolution of the clip
    scaling_factor = (clip.h / 1080)
    font_size = int(42 * scaling_factor)

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
        fontsize=adjusted_font_size,
        font=font_path
    )
    longest_line_width, text_height = temp_subtitle_clip.size

    subtitle_clip = TextClip(
        wrapped_text,
        fontsize=adjusted_font_size,
        color=color,
        # stroke_color="white",
        stroke_width=0,
        font=font_path,
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




def adjust_segment_properties(segment: VideoFileClip, original: VideoFileClip) -> VideoFileClip:
    segment = segment.set_fps(original.fps)
    segment = segment.set_duration(segment.duration)
    return segment



def replace_video_segments(
    original_segments: List[VideoFileClip],
    replacement_videos: Dict[int, VideoFileClip],
    subtitles: pysrt.SubRipFile,
    original_video: VideoFileClip,
    font_customization : [],
    resolution:str,
    subtitle_box_color,   
    
) -> List[VideoFileClip]:
    combined_segments = original_segments.copy()
    for replace_index in range(len(replacement_videos)):
        if 0 <= replace_index < len(combined_segments):
            target_duration = combined_segments[replace_index].duration
            start = subriptime_to_seconds(subtitles[replace_index].start)
            end = subriptime_to_seconds(subtitles[replace_index].end)

            # Adjust replacement video duration to match target duration

            if replacement_videos[replace_index].duration < target_duration:
                replacement_segment = loop(replacement_videos[replace_index], duration=target_duration)
            else:
                replacement_segment = replacement_videos[replace_index].subclip(0, target_duration)

            adjusted_segment = adjust_segment_properties(replacement_segment, original_video,)
            # add_subtitles_to_clip(subtitle_box_color=subtitle_box_color,clip=adjusted_segment,subtitle=subtitles[replace_index],base_font_size=font_customization[2],color=int(font_customization[1]),margin=font_customization[])
            adjusted_segment_with_subtitles = add_subtitles_to_clip(subtitle_box_color,adjusted_segment, subtitles[replace_index],font_customization[2],font_customization[1],int(font_customization[4]),font_customization[0])
            combined_segments[replace_index] = adjusted_segment_with_subtitles
    # for replace_index, replacement_video in replacement_videos.items():
    #     if 0 <= replace_index < len(combined_segments):
    #         target_duration = combined_segments[replace_index].duration
    #         start = subriptime_to_seconds(subtitles[replace_index].start)
    #         end = subriptime_to_seconds(subtitles[replace_index].end)

    #         # Adjust replacement video duration to match target duration

    #         if replacement_video.duration < target_duration:
    #             replacement_segment = loop(replacement_video, duration=target_duration)
    #         else:
    #             replacement_segment = replacement_video.subclip(0, target_duration)

    #         adjusted_segment = adjust_segment_properties(replacement_segment, original_video,)
    #         # add_subtitles_to_clip(subtitle_box_color=subtitle_box_color,clip=adjusted_segment,subtitle=subtitles[replace_index],base_font_size=font_customization[2],color=int(font_customization[1]),margin=font_customization[])
    #         adjusted_segment_with_subtitles = add_subtitles_to_clip(subtitle_box_color,adjusted_segment, subtitles[replace_index],font_customization[2],font_customization[1],int(font_customization[4]),font_customization[0])
    #         combined_segments[replace_index] = adjusted_segment_with_subtitles

    return combined_segments


# Predefined resolutions
MAINRESOLUTIONS = {
    '1:1': 1/1,
    '16:9': 16/9,
    '4:5': 4/5,
    '9:16': 9/16
}


def concatenate_clips(clips, target_resolution=None, target_fps=None):
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
        if target_resolution:
            clip = clip.resize(newsize=target_resolution)  # Resize to target resolution
        if target_fps:
            clip = clip.set_fps(target_fps)  # Set frame rate to target fps
        processed_clips.append(clip)

    # Concatenate all video clips
    final_clip = concatenate_videoclips(processed_clips, method="compose")
    logging.info('Clip has been concatenated: ')
    return final_clip



def main():
    # if len(sys.argv) != 9:
    #     print("Usage: python process_video.py <text_file_path> <video_paths_str> <output_video_path> <voice_id> <api_key> <base_path> <textfile_id>")
    #     sys.exit(1)
    print(len(sys.argv))

    text_file = sys.argv[1]
    video_paths_str = sys.argv[2]
    output_video_path = sys.argv[3]
    voice_id = sys.argv[4]
    api_key = sys.argv[5]
    base_path = sys.argv[6]
    textfile_id = sys.argv[7]
    resolution = sys.argv[8]
    font_color = sys.argv[9]
    subtitle_box_color = sys.argv[10]
    font_file_path = sys.argv[11]
    font_size=sys.argv[12]
    font_customization=[font_file_path,font_color,font_size,subtitle_box_color,28]

    dir_s=os.path.join(base_path,f'{textfile_id}_progress.txt')
        
    # Convert video_paths_str back to Python objects
    # video_paths = json.loads(video_paths_str)

    # Example: Read the text file
    with open(text_file, 'r') as file:
        text = file.read()
    update_progress(10,dir_s)

        # Process each video clip here (add logic for MoviePy/Aeneas)
    replacement_base_folder = os.path.join(base_path,'downloads') # path of a base directory where videos will be downloaded
    output_audio_file=os.path.join(base_path,'text_audio',f'{textfile_id}_converted_audio.mp3')
    audio_file = convert_text_to_speech(text_file, voice_id, api_key,output_audio_file)
    print(f'audio_file: ',audio_file)
    logging.info('done with audio file ')
    # Save the final video at output_video path
    output_srt_file_path = os.path.join(base_path, 'srt_files', f'{textfile_id}_generated_srt_output.json')
    srt_file_path = generate_srt_file(audio_file, text_file, output_srt_file_path)
    if srt_file_path: 
        logging.info('done with srt file')

    with open(srt_file_path, 'r') as f:
        sync_map = json.load(f)
    # # Additional processing with Aeneas or any other operations
    # # ...
    print(sync_map)
    def convert_time(seconds):
        milliseconds = int((seconds - int(seconds)) * 1000)
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"
    update_progress(20,dir_s)

    aligned_output = []
    for index, fragment in enumerate(sync_map['fragments']):
        start = convert_time(float(fragment['begin']))
        end = convert_time(float(fragment['end']))
        text = fragment['lines'][0].strip()
        aligned_output.append(f"{index + 1}\n{start} --> {end}\n{text}\n")
    try:
        with open(video_paths_str, 'r') as file:
            video_clips_dict = json.load(file)
            print(video_clips_dict)
    except FileNotFoundError:
        print("The file was not found.")
    except json.JSONDecodeError:
        print("Error decoding JSON.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    num_segments=len(video_clips_dict)
    print('num_segments: ',num_segments)
    blank_vide_path= os.path.join(base_path,f'blank_vide_{textfile_id}.mp4')
    os.makedirs(os.path.dirname(blank_vide_path),exist_ok=True)
    blank_vide=generate_blank_video_with_audio(audio_file,srt_file_path,blank_vide_path,resolution)
    logging.info("Blank video generated successfully")
    blank_vide_clip= load_video_from_file(Path(blank_vide_path))
    logging.info("Video loaded successfully")
    subtitles=load_subtitles_from_json_to_srt(srt_file_path)
    print(subtitles)
    blank_video_segments, subtitle_segments = get_segments_using_srt(blank_vide_clip, subtitles)
    update_progress(30,dir_s)

    output_video_segments = []
    start = 0
    logging.info('output_video_segments is to start')
    for video_segment, new_subtitle_segment in zip(blank_video_segments, subtitles):
        end = subriptime_to_seconds(new_subtitle_segment.end)
        required_duration = end - start
        new_video_segment = adjust_segment_duration(video_segment, required_duration)
        
        output_video_segments.append(new_video_segment.without_audio())
        start = end
    logging.info('output_video_segments has stopped')

    replacement_video_files=extract_video_paths(video_paths_str)
    replacement_videos_per_combination=[]
    update_progress(40,dir_s)
    
    for replacement_video_file in replacement_video_files:
            replacement_video = load_video_from_file(replacement_video_file)
            cropped_replacement_video = crop_to_aspect_ratio(replacement_video, RESOLUTIONS[resolution]) #MAINRESOLUTIONS[resolution]
            
            logging.info(f"Replacement video {replacement_video_file} cropped to desired aspect ratio")
            if len(replacement_videos_per_combination) < len(replacement_video_files):
                replacement_videos_per_combination.append({})
            # replacement_videos_per_combination[replacement_video_files.index(replacement_video_file)][replace_index] = cropped_replacement_video    
    final_blank_video = concatenate_clips(blank_video_segments,target_resolution=RESOLUTIONS[resolution],target_fps=30)
    logging.info('Concatination Done')
    try:    
        final__blank_audio = final_blank_video.audio
    except Exception as e:
        logging.error(f"Error loading background music: {e}")
        return
        # final__blank_audio = final_blank_video.audio
    update_progress(50,dir_s)
    
    replacement_video_clips=[]
    for video_file in replacement_video_files:
        clip= load_video_from_file(video_file)
        replacement_video_clips.append(clip)
    logging.info('Done Clipping replacements')
    update_progress(55,dir_s)
    
    final_video_segments = replace_video_segments(output_video_segments, replacement_video_clips, subtitles, blank_vide_clip, font_customization, resolution, subtitle_box_color)
    concatenated_video = concatenate_clips(final_video_segments, target_resolution=RESOLUTIONS[resolution], target_fps=30)
    update_progress(60,dir_s)

    # Extract original audio from the blank video clip
    original_audio = blank_vide_clip.audio.subclip(0, min(concatenated_video.duration, blank_vide_clip.audio.duration))
    update_progress(65,dir_s)

    # Set audio to concatenated video
    final_video = concatenated_video.set_audio(original_audio)  # Removed overwriting with blank audio

    # Speed up the video and save
    final_video_speeded_up = os.path.join(base_path, 'tmp', f"output_variation{textfile_id}_speed-up.mp4")
    final_video_speeded_up = speed_up_video_with_audio(final_video, final_video_speeded_up, speed_factor=1)
    update_progress(70,dir_s)

    # Output file
    output_file = os.path.join(base_path, 'final', f"final_output_{textfile_id}.mp4")
    if os.path.exists(output_file):
        os.remove(output_file)
    update_progress(75,dir_s)

    # Create the necessary directories if they do not exist
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Write the final video file with audio
    
    final_video_speeded_up.write_videofile(os.path.normpath(output_file), codec="libx264", audio_codec="aac", temp_audiofile="temp-audio.m4a", remove_temp=True)

    update_progress(100,dir_s)
if __name__ == "__main__":
    main()
