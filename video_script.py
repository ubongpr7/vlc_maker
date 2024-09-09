
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
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
import pysrt

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
imagemagick_path = "convert" # Set the path to the ImageMagick executable
os.environ['IMAGEMAGICK_BINARY'] = imagemagick_path
change_settings({"IMAGEMAGICK_BINARY": imagemagick_path})

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



def adjust_segment_properties(self, segment: VideoFileClip) -> VideoFileClip:
    """
    Adjusts the properties of a video segment to match the settings from the TextFile instance.

    Args:
        segment (VideoFileClip): The segment to adjust.

    Returns:
        VideoFileClip: The adjusted video segment.
    """
    # Set the FPS of the segment to match the TextFile instance's FPS
    segment = segment.set_fps(self.fps)
    # Optionally adjust duration if needed, though usually duration is inherent to the segment itself
    segment = segment.set_duration(segment.duration)
    
    return segment
def add_subtitles(self) -> VideoFileClip:
    if not self.blank_video:
        raise ValueError("No blank video file provided.")
    if not self.srt_file:
        raise ValueError("No SRT file provided.")

    video_path = self.blank_video.path
    srt_file_path = self.srt_file.path
    font_path = self.font_file.path if self.font_file else os.path.join(os.getcwd(), 'data', "Montserrat-SemiBold.ttf")

    logging.info(f"Adding subtitles to video: {video_path}")

    # Load video
    clip = VideoFileClip(video_path)

    # Handle subtitle box color
    subtitle_box_color = self.subtitle_box_color or (1, .3, .5)
    if subtitle_box_color:
        subtitle_box_color = subtitle_box_color.strip(' #')
        values = [int(subtitle_box_color[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
        subtitle_box_color = tuple(values)

    # Load subtitles
    subtitles = pysrt.open(srt_file_path)

    # Calculate the scaling factor based on the resolution of the clip
    scaling_factor = (clip.h / 1080)
    font_size = int(self.font_size * scaling_factor)

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

    def add_subtitle(subtitle: pysrt.SubRipItem):
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
        margin=28
        subtitle_clip = TextClip(
            wrapped_text,
            fontsize=adjusted_font_size,
            color=self.font_color,
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

        box_position = ('center', clip.h - box_height - 2 * margin)
        subtitle_position = ('center', clip.h - box_height - 2 * margin + (box_height - text_height) / 2)

        box_clip = box_clip.set_position(box_position)
        subtitle_clip = subtitle_clip.set_position(subtitle_position)

        return CompositeVideoClip([clip, box_clip, subtitle_clip])

    # Add all subtitles to the video
    final_clip = CompositeVideoClip([clip])
    for subtitle in subtitles:
        final_clip = add_subtitle(subtitle)

    return final_clip



def subriptime_to_seconds(srt_time: pysrt.SubRipTime) -> float:
    return srt_time.hours * 3600 + srt_time.minutes * 60 + srt_time.seconds + srt_time.milliseconds / 1000.0



def replace_video_segments(
    self,
    original_segments: List[VideoFileClip],
    replacement_videos: Dict[int, VideoFileClip],
    subtitles: pysrt.SubRipFile,
    original_video: VideoFileClip
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

            # Use the instance method to adjust segment properties
            adjusted_segment = self.adjust_segment_properties(replacement_segment)

            # Add subtitles using the instance method
            adjusted_segment_with_subtitles = self.add_subtitles()

            combined_segments[replace_index] = adjusted_segment_with_subtitles

    return combined_segments

def concatenate_clips(self, clips):
    """
    Concatenates a list of VideoFileClip objects into a single video clip.
    This method is adapted to work with the TextFile instance.

    Args:
        clips (list): List of VideoFileClip objects to concatenate.

    Returns:
        VideoFileClip: The concatenated video clip.
    """
    # Prepare a list to store modified clips
    processed_clips = []

    # Get target resolution and FPS from TextFile fields
    target_resolution = MAINRESOLUTIONS.get(self.resolution, (1920, 1080))  # Default to '16:9' if resolution not found
    target_fps = self.fps

    for clip in clips:
        if target_resolution:
            clip = clip.resize(newsize=target_resolution)  # Resize to target resolution
        if target_fps:
            clip = clip.set_fps(target_fps)  # Set frame rate to target fps
        processed_clips.append(clip)

    # Concatenate all video clips
    final_clip = concatenate_videoclips(processed_clips, method="compose")
    logging.info('Clip has been concatenated.')
    return final_clip

def speed_up_video(self, speed_factor, output_video_path):
    """
    Speeds up the video file associated with this TextFile instance.

    Args:
        speed_factor (float): The factor by which to speed up the video.
        output_video_path (str): The path where the sped-up video will be saved.

    Returns:
        VideoFileClip: The sped-up video clip.
    """
    if not self.blank_video:
        raise ValueError("No blank video file associated with this TextFile instance.")

    # Load the video file
    video_path = self.blank_video.path
    input_video = VideoFileClip(video_path)

    # Speed up the video and audio
    sped_up_video = input_video.fx(speedx, speed_factor)

    # Write the sped-up video to the output path
    sped_up_video.write_videofile(output_video_path, codec='libx264', audio_codec='aac')

    # Return the sped-up video as a VideoClip object
    return sped_up_video


def get_segments_using_srt(self) -> (List[VideoFileClip], List[pysrt.SubRipItem]):
    """
    Get video segments and subtitles based on the SRT file and the blank video.

    Returns:
        Tuple of lists: (video_segments, subtitle_segments)
    """
    if not self.blank_video:
        raise FileNotFoundError("Blank video file is not available.")

    # Load the blank video
    video_clip = VideoFileClip(self.blank_video.path)
    
    # Load the SRT file
    srt_file_path = self.text_file.path.replace('.txt', '.srt')
    subtitles = pysrt.open(srt_file_path)

    subtitle_segments = []
    video_segments = []
    video_duration = video_clip.duration

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

        video_segment = video_clip.subclip(start, end)
        if video_segment.duration == 0:
            logging.warning(f"Video segment duration is zero for subtitle ({subtitle.text}). Skipping this segment.")
            continue

        subtitle_segments.append(subtitle)
        video_segments.append(video_segment)

    return video_segments, subtitle_segments

def load_subtitles(self):
    """Load subtitles from the SRT file."""
    if not self.srt_file:
        raise ValueError("SRT file is not available.")
    srt_file_path = self.srt_file.path
    return pysrt.open(srt_file_path)

def generate_blank_video_with_audio(self, output_file, ):
    """
    Generates a blank video with the provided audio file and SRT subtitles.
    """
    # Ensure audio file exists
    resolution= self.resolution
    if not self.audio_file or not self.srt_file:
        raise ValueError("Audio file and SRT file must be provided before generating the video.")

    # Get durations from audio and SRT files
    srt_duration = self.get_video_duration_from_srt(self.srt_file.path)
    audio_clip = AudioFileClip(self.audio_file.path)
    audio_duration = audio_clip.duration

    # Determine the maximum duration
    duration = max(srt_duration, audio_duration)

    
    if resolution in RESOLUTIONS:
        width, height = RESOLUTIONS[resolution]
    else:
        raise ValueError(f"Resolution '{resolution}' is not supported. Choose from {list(RESOLUTIONS.keys())}.")

    # Create a blank (black) video clip with the desired resolution and duration
    blank_clip = ColorClip(size=(width, height), color=(0, 0, 0)).set_duration(duration)

    # Combine audio with blank video
    final_video = CompositeVideoClip([blank_clip]).set_audio(audio_clip)

    # Write the final video to the output file
    final_video.write_videofile(output_file, fps=24)
    self.blank_video=output_file
    self.save()
    return self.blank_video

def generate_srt_file(self):
    """
    Generates an SRT file using Aeneas from the text_file and audio_file.
    """
    # Define paths
    audio_file_path = self.audio_file.path
    text_file_path = self.text_file.path
    output_srt_file_path = os.path.join(settings.MEDIA_ROOT, 'srt_files', f'{self.pk}_output.srt')

    # Aeneas command to generate SRT
    command = f'python3.10 -m aeneas.tools.execute_task "{audio_file_path}" "{text_file_path}" ' \
                f'"task_language=eng|is_text_type=plain|os_task_file_format=srt" "{output_srt_file_path}"'

    try:
        # Run the command using subprocess
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Check for errors in subprocess execution
        if result.returncode == 0:
            self.srt_file = output_srt_file_path  # Save the path of the generated SRT file to the model
            self.save()  # Save the updated model instance with the SRT file path
            logging.info(f'SRT file generated successfully: {output_srt_file_path}')
        else:
            logging.error(f'Error generating SRT file: {result.stderr.decode("utf-8")}')
    except Exception as e:
        logging.error(f'An unexpected error occurred while generating SRT file: {e}')

def resize_to_aspect_ratio(self, video_path: str) -> VideoFileClip:
    """
    Resize the video while maintaining its original aspect ratio to fit within the desired aspect ratio specified by this TextFile's resolution field.

    Args:
        video_path (str): The path to the video file.

    Returns:
        VideoFileClip: The resized video clip.
    """
    # Load the video from the path
    video = VideoFileClip(video_path)

    # Get the desired aspect ratio from the resolution field
    desired_aspect_ratio = MAINRESOLUTIONS.get(self.resolution, 16/9)  # Default to 16:9 if resolution not found

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


def load_video_from_file(self,file: Path) -> VideoFileClip:
    # if not file.exists():
    #     raise FileNotFoundError(f"Video file not found: {file}")
    return VideoFileClip(os.path.normpath(file))

def get_video_duration_from_srt(self, ):
    """
    Extracts the duration from the SRT file.
    Assumes that the last subtitle's end time is the duration.
    """
    srt_file=self.srt_file
    max_time = 0.0
    try:
        with open(srt_file, 'r') as file:
            for line in file:
                if '-->' in line:
                    timecodes = line.split('-->')
                    end_time = timecodes[1].strip().split(',')[0].strip()
                    hours, minutes, seconds = end_time.split(':')
                    seconds_total = float(hours) * 3600 + float(minutes) * 60 + float(seconds)
                    max_time = max(max_time, seconds_total)
    except Exception as e:
        logging.error(f"Failed to calculate video duration from SRT file: {e}")
    return max_time

def convert_text_to_speech(self):
    """
    Converts the entire text file to speech and saves the audio file in the 'audio_files/' directory.
    """
    try:
        # Open the text file for reading
        with open(self.text_file.path, "r") as text_file:  # Use `path` instead of `url`
            text = text_file.read().strip()  # Read and remove leading/trailing whitespace
            print(text)

        # Initialize ElevenLabs client
        client = ElevenLabs(api_key=self.api_key)
        
        # Generate voice from the read text
        audio_data = client.generate(
            text=text,
            voice=Voice(
                voice_id=self.voice_id,
                settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
            )
        )

        # Save the audio to a temporary file
        audio_temp_path = os.path.join(settings.MEDIA_ROOT, 'audio_files', f'{self.text_file.name}_{self.pk}_output.mp3')
        with open(audio_temp_path, 'wb') as audio_file:
            audio_file.write(audio_data)  # Write binary audio data to file
        
        # Open the saved file and assign it to the audio_file field
        with open(audio_temp_path, 'rb') as f:
            self.audio_file.save(f'{self.text_file.name}_{self.pk}_output.mp3', File(f))

        # Save the model to update the audio_file field in the database
        self.save()
        logging.info(f"Audio file saved successfully to: {self.audio_file.path}")

    except FileNotFoundError:
        print("Error: The specified text file was not found.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return self.audio_file.path

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

def load_subtitles_from_file(self) -> pysrt.SubRipFile:
    if not self.srt_file:
        raise FileNotFoundError("SRT file does not exist.")
    return pysrt.open(self.srt_file.path)

def get_segments_using_srt(self) -> (List[VideoFileClip], List[pysrt.SubRipItem]):
    """
    Get video segments based on the SRT file associated with this TextFile.

    Returns:
        tuple: (list of VideoFileClip segments, list of SubRipItem subtitles)
    """
    subtitles = self.load_subtitles_from_file()
    video = VideoFileClip(self.blank_video.path)
    video_segments = []
    subtitle_segments = []
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

def get_subtitle_count(self) -> int:
    """
    Get the number of subtitles from the SRT file.

    Returns:
        int: Number of subtitles in the SRT file
    """
    if not self.srt_file:
        return 0

    subtitles = self.load_subtitles_from_file()
    return len(subtitles)


def main():
    pass

if __name__ == "__main__":
    main()