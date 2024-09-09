import logging
from pathlib import Path
from typing import List, Dict
import os
import re
import pysrt
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
from elevenlabs import Voice, VoiceSettings, play, save
from elevenlabs.client import ElevenLabs
import subprocess
import json
import sys
import moviepy.video.fx.all as vfx
# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
imagemagick_path = "convert" # Set the path to the ImageMagick executable
os.environ['IMAGEMAGICK_BINARY'] = imagemagick_path
elevenlabs_api_key = sys.argv[4]
client = ElevenLabs(api_key=elevenlabs_api_key)
# You can also set the MoviePy config
change_settings({"IMAGEMAGICK_BINARY": imagemagick_path})

openai.api_key = 'sk-proj-mo9iZjhl3DNjXlxMcx1FT3BlbkFJz5UCGoPBLnSQhh2b2stB' # write your openai api
PEXELS_API_KEY = 'ljSCcK6YYuU0kNyMTADStB8kSOWdkzHCZnPXc26QEHhaHYqeXusdnzaA' # write your pexels
# Base URL for Pexels API
BASE_URL = 'https://api.pexels.com/videos/search'

# Paths for existing video clips
def get_local_video_paths(data_folder: str) -> Dict[str, str]:
    """
    Scans the specified data folder and returns a dictionary with folder names as keys and their paths as values.
    Only includes directories that contain .mp4 video files.
    """
    video_paths = {}
    for category in os.listdir(data_folder):
        category_path = os.path.join(data_folder, category)
        if os.path.isdir(category_path):
            # Check if the directory contains .mp4 files
            if any(file.endswith('.mp4') for file in os.listdir(category_path)):
                video_paths[category] = category_path
    return video_paths

# Get the dynamic video paths
local_video_paths = get_local_video_paths('data')
print(local_video_paths)  # This will print the dictionary of folder names and their paths

# Function to get keywords from ChatGPT
def get_keywords_for_line(line):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user",
             "content": f"Give the best search keywords to find a relevant video on Pexels for the following line about an elderly person: '{line}'"}
        ],
        max_tokens=100,
        temperature=1,
        top_p=0.95,
        n=1,
        stop=None
    )
    keywords = response['choices'][0]['message']['content']
    return keywords.strip()


def save_audio(audio_data, filename="output_of_lead_kyrona.mp3"):
  with open(filename, "wb") as f:
    f.write(audio_data)
    print(f"Audio saved to: {filename}")


# Function to search for videos
def search_videos(query, per_page=15, page=1):
    headers = {
        'Authorization': PEXELS_API_KEY
    }
    params = {
        'query': query,
        'per_page': per_page,
        'page': page
    }
    response = requests.get(BASE_URL, headers=headers, params=params)
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Failed to search videos: {response.status_code}")
        return None


# Function to find the HD video file with the highest number of likes and correct dimensions
def get_best_hd_file(videos):
    best_video = None
    best_file = None
    highest_likes = -1
    desired_aspect_ratio = 16 / 9  # Standard HD aspect ratio

    print("Total Videos:", len(videos))  # Log total videos

    # Iterate over each video
    for video in videos:
        for file in video['video_files']:
            width = file['width']
            height = file['height']
            aspect_ratio = width / height
            likes = video.get('likes', 0)

            print(f"Evaluating file: Width: {width}, Height: {height}, Aspect Ratio: {aspect_ratio}, Likes: {likes}")

            # Check if this file meets relaxed criteria for HD
            if width >= 1280 and height >= 720 and abs(aspect_ratio - desired_aspect_ratio) <= 0.2:
                print("File meets primary HD criteria")
                if likes > highest_likes:
                    highest_likes = likes
                    best_video = video
                    best_file = file

            # If no video meets the relaxed criteria, broaden further
            if not best_file:
                # Check if the file is a minimum of 720p or any widescreen
                if (width >= 1024 and height >= 576) or (aspect_ratio >= 1.5 and width >= 1024):
                    print("File meets secondary criteria")
                    if likes > highest_likes:
                        highest_likes = likes
                        best_video = video
                        best_file = file

    # Fallback to the first available video if no suitable video is found
    if not best_file and videos:
        print("No file met criteria, falling back to first available video")
        for video in videos:
            file = video['video_files'][0]  # Pick the first available file
            likes = video.get('likes', 0)
            if likes > highest_likes:
                highest_likes = likes
                best_video = video
                best_file = file

    return best_video, best_file



# Function to download video
def download_video(video_url, output_file):
    response = requests.get(video_url, stream=True)
    if response.status_code == 200:
        with open(output_file, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                file.write(chunk)
        logging.info(f'Video downloaded successfully: {output_file}')
    else:
        logging.error('Failed to download video')


# Function to categorize script lines using ChatGPT
# def categorize_script_lines(script):
#     response = openai.ChatCompletion.create(
#         model="gpt-4-turbo",
#         messages=[
#             {"role": "system", "content": "You are a helpful assistant."},
#             {"role": "user", "content": f"""
#             From this script im sending you now can you put a bracket on what lines you think I should put a “Neck Pain Clips”

# and what lines I should put the “Compressed Spine Clips”

# and what lines i should put "Disc Bulging Clips"

# and what lines i should put "Head Forward Clips"

# and what lines I should put “Product Animation Clips”

# and what lines I should put “Decompressed Spine Clips”

# if any line in the script isn't suitable for these 6 folders just write "No Category". here is the script please put the bracket on just the categories mentioned above for heir respective lines also remember only one folder per line:
# {script}"""}
#         ],
#         max_tokens=1500,
#         temperature=0.7,
#         top_p=1.0,
#         n=1,
#         stop=None
#     )
#     categorized_script = response['choices'][0]['message']['content']
#     return categorized_script



def load_subtitles_from_txt_file(srt_file: Path) -> pysrt.SubRipFile:
    # if not srt_file.exists():
    #     raise FileNotFoundError(f"SRT File not found: {srt_file}")
    return pysrt.open(srt_file)


def get_segments_using_srt_file(srt_file: Path) -> int:
    subtitles = load_subtitles_from_txt_file(srt_file)
    return len(subtitles)


def get_video_duration_from_srt(srt_file):
    with open(srt_file, 'r') as file:
        content = file.read()
    timestamps = re.findall(r'\d{2}:\d{2}:\d{2},\d{3}', content)
    end_times = timestamps[1::2]  # Get all end times
    last_end_time = end_times[-1] if end_times else "00:00:00,000"
    h, m, s_ms = last_end_time.split(':')
    s, ms = s_ms.split(',')
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


# Predefined resolutions
RESOLUTIONS = {
    '1:1': (480, 480),
    '16:9': (1920, 1080),
    '4:5': (800, 1000),
    '9:16': (1080, 1920)
}



def generate_blank_video_with_audio(audio_file, srt_file, output_file, resolution='16:9'):
    # Get the duration from the SRT file
    srt_duration = get_video_duration_from_srt(srt_file)

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


def load_video_from_file(file: Path) -> VideoFileClip:
    # if not file.exists():
    #     raise FileNotFoundError(f"Video file not found: {file}")
    return VideoFileClip(os.path.normpath(file))




# docker run -v /mnt/c/Users/Francis/Desktop/dev/Project/app:/app -p 8080:5000 -it nas415/vsl_generator
def crop_to_aspect_ratio(video: VideoFileClip, desired_aspect_ratio: float) -> VideoFileClip:
    video_aspect_ratio = video.w / video.h
    if video_aspect_ratio > desired_aspect_ratio:
        new_width = int(desired_aspect_ratio * video.h)
        new_height = video.h
        x1 = (video.w - new_width) // 2
        y1 = 0
    else:
        new_width = video.w
        new_height = int(video.w / desired_aspect_ratio)
        x1 = 0
        y1 = (video.h - new_height) // 2
    x2 = x1 + new_width
    y2 = y1 + new_height
    cropped_video= crop(video, x1=x1, y1=y1, x2=x2, y2=y2)
    return cropped_video
    # cropped_video.write_videofile(os.path.join(os.getcwd(),'cropped','video.mp4'), codec='libx264', audio_codec='aac')

def resize_to_aspect_ratio(video: VideoFileClip, desired_aspect_ratio: float) -> VideoFileClip:
    """
    Resize the video while maintaining its original aspect ratio to fit within the desired aspect ratio.

    Args:
        video (VideoFileClip): The original video clip.
        desired_aspect_ratio (float): The desired aspect ratio (width/height).

    Returns:
        VideoFileClip: The resized video clip.
    """
    # Calculate the current aspect ratio of the video
    video_aspect_ratio = video.w / video.h

    # Determine how to scale the video based on the desired aspect ratio
    if video_aspect_ratio > desired_aspect_ratio:
        # Video is wider than desired aspect ratio, fit to width
        new_width = video.w
        new_height = int(video.w / desired_aspect_ratio)
    else:
        # Video is taller than desired aspect ratio, fit to height
        new_width = int(video.h * desired_aspect_ratio)
        new_height = video.h

    # Resize the video to the new dimensions while preserving the original aspect ratio
    resized_video = video.resize(newsize=(new_width, new_height))

    return resized_video

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


def load_subtitles_from_file(srt_file: Path) -> pysrt.SubRipFile:
    
    return pysrt.open(srt_file)


def adjust_segment_duration(segment: VideoFileClip, duration: float) -> VideoFileClip:
    current_duration = segment.duration
    if current_duration < duration:
        return loop(segment, duration=duration)
    elif current_duration > duration:
        return segment.subclip(0, duration)
    return segment







# Define supported resolutions



def adjust_segment_properties(segment: VideoFileClip, original: VideoFileClip) -> VideoFileClip:
    segment = segment.set_fps(original.fps)
    segment = segment.set_duration(segment.duration)
    return segment




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
    font_size = int(base_font_size * scaling_factor)

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


def replace_video_segments(
    original_segments: List[VideoFileClip],
    replacement_videos: Dict[int, VideoFileClip],
    subtitles: pysrt.SubRipFile,
    original_video: VideoFileClip,
    font_customization : [],
    subtitle_box_color,   
    # base_font_size,
    # color,
    # margin,
    # font_path,
) -> List[VideoFileClip]:
    combined_segments = original_segments.copy()
    for replace_index, replacement_video in replacement_videos.items():
        if 0 <= replace_index < len(combined_segments):
            target_duration = combined_segments[replace_index].duration
            start = subriptime_to_seconds(subtitles[replace_index].start)
            end = subriptime_to_seconds(subtitles[replace_index].end)

            # Adjust replacement video duration to match target duration

            if replacement_video.duration < target_duration:
                replacement_segment = loop(replacement_video, duration=target_duration)
            else:
                replacement_segment = replacement_video.subclip(0, target_duration)

            adjusted_segment = adjust_segment_properties(replacement_segment, original_video,)
            # add_subtitles_to_clip(subtitle_box_color=subtitle_box_color,clip=adjusted_segment,subtitle=subtitles[replace_index],base_font_size=font_customization[2],color=int(font_customization[1]),margin=font_customization[])
            adjusted_segment_with_subtitles = add_subtitles_to_clip(subtitle_box_color,adjusted_segment, subtitles[replace_index],font_customization[2],font_customization[1],int(font_customization[4]),font_customization[0])
            combined_segments[replace_index] = adjusted_segment_with_subtitles

    return combined_segments



def speed_up_video_with_audio(input_video, output_video_path, speed_factor):
    # Speed up the video and audio using speedx
    sped_up_video = input_video.fx(vfx.speedx, speed_factor)

    # Write the sped-up video to the output path
    # sped_up_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')

    # Return the sped-up video as a VideoClip object
    return sped_up_video


def add_background_music(final_video: VideoFileClip, background_music_file: str) -> VideoFileClip:
    try:
        # Load the background music
        background_music = AudioFileClip(os.path.normpath(background_music_file))
        
        # Adjust the duration of the background music to match the video duration
        if background_music.duration < final_video.duration:
            # Loop the music if it's shorter than the video duration
            background_music = background_music.fx(vfx.loop, duration=final_video.duration)
        else:
            # Trim the music if it's longer than the video duration
            background_music = background_music.subclip(0, final_video.duration)
        
        # Mix the video's original audio with the background music
        final_audio = CompositeAudioClip([final_video.audio, background_music.volumex(0.1)])
    except Exception as e:
        logging.error(f"Error loading background music: {e}")
        # Fallback to original audio if there's an error
        final_audio = final_video.audio

    # Set the combined audio back to the video
    final_video = final_video.set_audio(final_audio)
    return final_video


def process_video_background(video_path, music_files):
    # video_clip = VideoFileClip(video_path)

    # # Prepare audio clips
    # audio_clips = []
    # for music_file in music_files:
    #     music_path = f'tmp/{music_file.filename}'
    #     music_file.save(music_path)
    #     audio_clip = AudioFileClip(music_path)
    #     audio_clips.append(audio_clip)

    # # Combine audio clips
    # final_audio = concatenate_audioclips(audio_clips)

    # # Set audio to video
    # final_video = video_clip.set_audio(final_audio)

    # final_path = 'static/final_video.mp4'
    # final_video.write_videofile(final_path, codec='libx264')

    return 
    # return final_path



# Predefined resolutions
MAINRESOLUTIONS = {
    '1:1': 1/1,
    '16:9': 16/9,
    '4:5': 4/5,
    '9:16': 9/16
}

def update_progress(progress):
    with open('progress.txt', 'w') as f:
        f.write(str(progress))


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
    print("sys.argv",sys.argv)
    category_file = sys.argv[3]
    elevenlabs_api_key = sys.argv[4]  # ElevenLabs API key
    script_file = sys.argv[1]  #'Lead Kyrona.txt' # enter path for your script file
    voice_id = sys.argv[2]  # Voice ID


    #subtilte inputs
    font_file_path = sys.argv[5]
    font_color = sys.argv[6]
    font_size = float(sys.argv[7])
    subtitle_box_color = sys.argv[8]
    margin = int(sys.argv[9])
    resolution = sys.argv[10]
    # music_path_ = sys.argv[11]

    print("subtitle",subtitle_box_color)
    print('Resoution from PR7: ',resolution)
    # sys.exit()
    update_progress(1)
    font_customization=[font_file_path,font_color,font_size,subtitle_box_color,margin]

    try:
        # Open the text file for reading
        with open(script_file, "r") as text_file:
            text = text_file.read().strip()  # Read and remove leading/trailing whitespace
            print(text)

        # Generate voice from the read text
        audio_data = client.generate(
            text=text,
            voice=Voice(
                voice_id=voice_id,
                settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
            )
        )

        # Save the audio to a file
        save(audio_data, os.path.join(os.getcwd(), "tmp", 'output_of_lead_kyrona.mp3'))
        logging.info('output_of_lead_kyrona.mp3 generated successfully')

    except FileNotFoundError:
        print("Error: The specified file 'Script File.txt' was not found.")
        return

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return
    
    update_progress(5)
    # Set encoding to UTF-8
    os.environ['PYTHONIOENCODING'] = 'UTF-8'
    
    print("hellow rold")

    # Define file paths
    audio_file = os.path.join(os.getcwd(), "tmp", 'output_of_lead_kyrona.mp3') #path for mp3 file
    output_video_file = os.path.join(os.getcwd(), "tmp", 'output_video.mp4') # path for the output video
    replacement_base_folder = os.path.join(os.getcwd(), "tmp", 'downloads') # path of a base directory where videos will be downloaded
    # if music_path_:

    #     background_music_file = os.path.join(os.getcwd(),music_path_)
    # else:
    #     # background_music_file = os.path.join(os.getcwd(), "data", 'data.mpeg')
    video_folder = os.path.join(os.getcwd(),"data")
    output_base_folder = replacement_base_folder
    output_srt_file_path = script_file.replace(".txt", "_aligned.json")
    update_progress(10)
    # Adjust the subprocess command to use the correct paths and encoding
    command = f'python3.10 -m aeneas.tools.execute_task "{audio_file}" "{script_file}" "task_language=eng|is_text_type=plain|os_task_file_format=json" "{output_srt_file_path}"'
    result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Print command output for debugging
    print("Command output:", result.stdout.decode('utf-8'))
    print("Command error:", result.stderr.decode('utf-8'))

    # Verify if the output file was created
    if not Path(output_srt_file_path).exists():
        raise FileNotFoundError(
            f"The output file {output_srt_file_path} was not created. Check the command output above for errors.")

    # Read and parse the output file
    with open(output_srt_file_path, 'r') as f:
        sync_map = json.load(f)
    update_progress(15)

    # Convert seconds to hours:minutes:seconds,milliseconds format
    def convert_time(seconds):
        milliseconds = int((seconds - int(seconds)) * 1000)
        minutes, seconds = divmod(int(seconds), 60)
        hours, minutes = divmod(minutes, 60)
        return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}"

    # Process the output to make it SRT readable
    aligned_output = []
    for index, fragment in enumerate(sync_map['fragments']):
        start = convert_time(float(fragment['begin']))
        end = convert_time(float(fragment['end']))
        text = fragment['lines'][0].strip()
        aligned_output.append(f"{index + 1}\n{start} --> {end}\n{text}\n")

    # Write output to a new text file in SRT format
    srt_file = script_file.replace(".txt", "_with_timestamps.srt")
    with open(srt_file, 'w') as file:
        for line in aligned_output:
            file.write(line + "\n")
    update_progress(20)

    try:
        # Ensure the folder exists and remove its contents
        if os.path.exists(replacement_base_folder) == True and os.path.isdir(replacement_base_folder):
            shutil.rmtree(replacement_base_folder)
            print(f"Contents of {replacement_base_folder} have been removed.")

        # Recreate the folder (optional)
        os.makedirs(replacement_base_folder, exist_ok=True)
        print(f"{replacement_base_folder} created successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")
    update_progress(25)

    # Read the script lines from the text file
    with open(script_file, 'r') as file:
        script_lines = file.read()

    with open(category_file, 'r') as file:
        category_lines = file.readlines()
    update_progress(30)

    # Categorize the script lines
    local_video_paths = {}
    for line in category_lines:
        topic_folder, selected_video = os.path.split(line.strip())
        if topic_folder not in local_video_paths:
            local_video_paths[topic_folder] = []
        local_video_paths[topic_folder].append(os.path.join(topic_folder, selected_video))
    num_segments = get_segments_using_srt_file(srt_file)
    

    update_progress(35)
    print("local video path", local_video_paths)

    unclassified_lines = []
    processed_videos = set()  # Initialize a set to track processed videos
    downloaded_segments = set()

    # Process each segment
    for index in range(num_segments):
        if index < len(category_lines):
            line_with_category = category_lines[index]
            category,video = line_with_category.split("/")
            category = category.strip()
            video = video.strip()

            logging.debug(f"Processing segment {index + 1}: Video: {video}, Category: {category}")

            if line and category != 'No Category':
                category_path = local_video_paths.get(category)

                print("category_apth",category_path)

                if category_path:
                    video_files = category_path
                    logging.debug(f"Found {len(video_files)} unprocessed local video(s) for category '{category}'")
                else:
                    video_files = []
                    logging.warning(f"No local video files found for category '{category}' or directory does not exist")

                if video_files:
                    video_file = os.path.join(video_folder,video_files[0])  # Use the first unprocessed file
                    segment_folder = os.path.join(output_base_folder, str(index + 1))
                    os.makedirs(segment_folder, exist_ok=True)
                    output_file = os.path.join(segment_folder, os.path.basename(video_files[0].split("/")[1]))
                    try:
                        shutil.copy(video_file, output_file)  # Copy the local video to the segment folder
                        logging.info(f'Using local video: {video_file} for segment {index + 1}')
                        processed_videos.add(video_file)  # Add the processed video to the set
                        downloaded_segments.add(index + 1)
                    except FileNotFoundError as e:
                        logging.error(f"File not found: {video_file}. Skipping to next file.")
                else:
                    logging.warning(f"No local video files found for category '{category}' or directory does not exist")
                    unclassified_lines.append((index + 1, line))
            else:
                unclassified_lines.append((index + 1, line))
        else:
            logging.warning(f"No script line found for segment {index + 1}")

    # Print or log any unclassified lines
    if unclassified_lines:
        logging.warning(f"Unclassified lines: {unclassified_lines}")
    update_progress(40)

    # Process unclassified lines
    for index, line in unclassified_lines:
        keywords = get_keywords_for_line(line)
        result = search_videos(keywords)
        if result:
            best_video, best_file = get_best_hd_file(result['videos'])
            if best_video and best_file:
                video_url = best_file['link']
                segment_folder = os.path.join(output_base_folder, str(index))
                os.makedirs(segment_folder, exist_ok=True)
                safe_filename = f'{line[:10].replace(" ", "_").replace("/", "_")}.mp4'
                output_file = os.path.join(segment_folder, safe_filename)
                if output_file not in processed_videos:  # Ensure not to download same video multiple times
                    download_video(video_url, output_file)
                    processed_videos.add(output_file)  # Track the processed video
                    downloaded_segments.add(index)
            else:
                logging.warning(f"No suitable HD video found for keywords: {keywords}")
        else:
            logging.warning(f"No results found for keywords: {keywords}")
    update_progress(45)

    # Ensure all segments have videos
    # lines_with_categories=[]
    missing_segments = set(range(1, num_segments + 1)) - downloaded_segments
    try:

        for missing_index in missing_segments:
            if missing_index <= len(lines_with_categories):
                line_with_category = lines_with_categories[missing_index - 1]
                if '[' not in line_with_category:
                    line = line_with_category.strip()
                else:
                    line = line_with_category.rsplit('[', 1)[0].strip()

                logging.warning(f"Missing video for segment {missing_index}, retrying...")

                # Get keywords and download video
                keywords = get_keywords_for_line(line)
                result = search_videos(keywords)
                if result:
                    best_video, best_file = get_best_hd_file(result['videos'])
                    if best_video and best_file:
                        video_url = best_file['link']
                        segment_folder = os.path.join(output_base_folder, str(missing_index))
                        os.makedirs(segment_folder, exist_ok=True)
                        safe_filename = f'{line[:10].replace(" ", "_").replace("/", "_")}.mp4'
                        output_file = os.path.join(segment_folder, safe_filename)
                        if output_file not in processed_videos:  # Ensure not to download same video multiple times
                            download_video(video_url, output_file)
                            processed_videos.add(output_file)  # Track the processed video
                            downloaded_segments.add(missing_index)
                    else:
                        logging.warning(f"No suitable HD video found for keywords: {keywords}")
                else:
                    logging.warning(f"No results found for keywords: {keywords}")
    except Exception as e:
        logging.error(e)
    output_folder = Path("output")
    output_folder.mkdir(parents=True, exist_ok=True)
    update_progress(50)

    # Generate the blank video with the audio and SRT file
    generate_blank_video_with_audio(audio_file, srt_file, output_video_file,resolution)
    logging.info("Blank video generated successfully")

    # Process the generated video
    video = load_video_from_file(Path(output_video_file))
    # print(f'output_video_file Pr72',output_video_file)
    logging.info("Video loaded successfully")
    # cropped_video = crop_to_aspect_ratio(video, 4 / 5)
    # logging.info("Video cropped to desired aspect ratio")
    subtitles = load_subtitles_from_file(Path(srt_file))
    logging.info("Loaded SRT Subtitles from the provided subtitle file")
    video_segments, subtitle_segments = get_segments_using_srt(video, subtitles)
    logging.info("Segmented Input video based on the SRT Subtitles generated for it")
    output_video_segments = []
    start = 0
    update_progress(55)
    logging.info('output_video_segments is to start')
    for video_segment, new_subtitle_segment in zip(video_segments, subtitles):
        end = subriptime_to_seconds(new_subtitle_segment.end)
        required_duration = end - start
        new_video_segment = adjust_segment_duration(video_segment, required_duration)
        
        output_video_segments.append(new_video_segment.without_audio())
        start = end
    update_progress(60)
    logging.info('output_video_segments has stopped')

    replacement_videos_per_combination = []

    # Load replacement videos from subfolders and organize by segment index
    for folder in os.listdir(replacement_base_folder):
        folder_path = os.path.join(replacement_base_folder, folder)
        if not os.path.isdir(folder_path):
            continue
        folder_name = folder
        if not folder_name.isdigit():
            logging.warning(f"Folder name {folder_name} is not a valid segment index. Skipping...")
            continue
        replace_index = int(folder_name) - 1
        replacement_video_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.mp4')]
        logging.info(f"Found {len(replacement_video_files)} replacement video files in {folder}")
        for replacement_video_file in replacement_video_files:
            replacement_video = load_video_from_file(replacement_video_file)
            cropped_replacement_video = resize_to_aspect_ratio(replacement_video, MAINRESOLUTIONS[resolution]) #MAINRESOLUTIONS[resolution]
            
            logging.info(f"Replacement video {replacement_video_file} cropped to desired aspect ratio")
            if len(replacement_videos_per_combination) < len(replacement_video_files):
                replacement_videos_per_combination.append({})
            replacement_videos_per_combination[replacement_video_files.index(replacement_video_file)][replace_index] = cropped_replacement_video
    print('the replacement_videos_per_combination: ',replacement_videos_per_combination)
    update_progress(65)
    logging.info('Concatination about to begin')
    # Generate videos with all combinations of replacements
    final_video = concatenate_clips(video_segments,target_resolution=RESOLUTIONS[resolution],target_fps=30)

    logging.info('Concatination Done')

    try:
        
        final_audio = final_video.audio
    except Exception as e:
        logging.error(f"Error loading background music: {e}")
        final_audio = final_video.audio

        # final_video = final_video.set_audio(final_audio)
    update_progress(70)

    for i, replacement_videos in enumerate(replacement_videos_per_combination):
        final_video_segments = replace_video_segments(output_video_segments, replacement_videos, subtitles, video,font_customization,resolution,subtitle_box_color)
        concatenated_video = concatenate_clips(final_video_segments,target_resolution=RESOLUTIONS[resolution],target_fps=30)
        original_audio = video.audio.subclip(0, min(concatenated_video.duration, video.audio.duration))
        final_video_with_audio = concatenated_video.set_audio(original_audio)
        final_video = final_video_with_audio.set_audio(final_audio)
        final_video_speeded_up = os.path.join(os.getcwd(), 'tmp', f"output_variation{i + 1}_speed-up.mp4")
        final_video_speeded_up = speed_up_video_with_audio(final_video, final_video_speeded_up, speed_factor=1)
        output_file = os.path.join(os.getcwd(), 'static', 'final', f"output_variation{i + 1}.mp4")
        final_video_speeded_up.write_videofile(os.path.normpath(output_file), codec="libx264", audio_codec="aac")
        logging.info(f"Generated output video: {output_file}")
    update_progress(100)

if __name__ == "__main__":
    main()
