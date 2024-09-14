from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_audioclips, CompositeAudioClip, CompositeVideoClip
import os
import sys
import json
import moviepy.video.fx.all as vfx
from moviepy.config import change_settings

# Configure logging (if needed for debugging)
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Set the path to ImageMagick executable
imagemagick_path = "convert"
os.environ['IMAGEMAGICK_BINARY'] = imagemagick_path
change_settings({"IMAGEMAGICK_BINARY": imagemagick_path})

def update_progress(progress,dir_s):
    with open(dir_s, 'w') as f:
        f.write(str(progress))


def process_video(video_path, music_info_path,textfile_id,base_dir):
    with open(music_info_path, 'r') as f:
        music_info = f.readlines()
        
    dir_s= os.path.join(base_dir,f'{textfile_id}_progress.txt')
    update_progress(2,dir_s)
    # Load the video clip
    video_clip = VideoFileClip(video_path)
    video_duration = video_clip.duration

    # Load the original audio from the video
    original_audio = video_clip.audio
    update_progress(5,dir_s)
    # List to hold individual background audio clips
    background_clips = []

    for line in music_info:
        music_path, start_time, end_time = line.strip().split(' ')
        start_time_seconds = float(start_time)
        end_time_seconds = float(end_time)
        duration = end_time_seconds - start_time_seconds
        
        if duration < 0:
            raise ValueError("End time must be greater than start time.")

        # Load and process the background music file
        # music_path=os.path.join('app',music_path)
        music_path=music_path.strip()
        if not os.path.exists(music_path):
            os.makedirs(os.path.dirname(music_path), exist_ok=True)
            
        background_clip = AudioFileClip(music_path).subclip(0, duration)
        background_clip = background_clip.set_start(start_time_seconds)

        # Append the processed background clip to the list
        background_clips.append(background_clip)

    # Create a composite audio clip with the background music
    background_audio = CompositeAudioClip(background_clips)
    update_progress(15,dir_s)
    # Combine the original audio with the background music
    if original_audio is not None:
        final_audio = CompositeAudioClip([original_audio.volumex(1.0), background_audio.volumex(0.1)])
    else:
        final_audio = background_audio
    update_progress(20,dir_s)
    # Adjust the final audio to match the video duration
    if final_audio.duration < video_duration:
        # Loop the audio if it's shorter than the video duration
        num_loops = int(video_duration / final_audio.duration) + 1
        final_audio = concatenate_audioclips([final_audio] * num_loops).subclip(0, video_duration)
    else:
        # Trim the audio if it's longer than the video duration
        final_audio = final_audio.subclip(0, video_duration)

    # Set the final audio to the video clip
    video_clip = video_clip.set_audio(final_audio)
    final_path = os.path.join(base_dir, 'finished', f'video_output_{textfile_id}.mp4')

    # Remove the existing file if it exists
    if os.path.exists(final_path):
        os.remove(final_path)

    # Create the necessary directories if they do not exist
    os.makedirs(os.path.dirname(final_path), exist_ok=True)

    # Write the video file with the proper codec
    video_clip.write_videofile(final_path, codec='libx264')

    update_progress(94,dir_s)
    # Close the clips to free resources
    video_clip.close()
    for clip in background_clips:
        clip.close()
    import time 
    time.sleep(6)
    update_progress(100,dir_s)
    return final_path

def parse_time(time_str):
    """Convert mm:ss time string to total seconds."""
    try:
        minutes, seconds = map(int, time_str.split(':'))
        return minutes * 60 + seconds
    except ValueError:
        raise ValueError("Invalid time format. Use mm:ss.")


if __name__ == "__main__":
    # Check if the correct number of arguments are passed
    if len(sys.argv) != 5:
        print("Usage: python process_video.py <video_path> <music_info_path>")
        sys.exit(1)

    video_path = sys.argv[1]
    music_info_path = sys.argv[2]
    textfile_id = sys.argv[3]
    base_dir=sys.argv[4]

    final_video_path = process_video(video_path, music_info_path,textfile_id,base_dir)
    print(f"Final video saved at: {final_video_path}")
