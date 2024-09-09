import sys
import json
import subprocess
import os
import logging
import uuid

import os
import logging
from elevenlabs.client  import ElevenLabs, Voice, VoiceSettings
from moviepy.config import change_settings


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
imagemagick_path = "convert" # Set the path to the ImageMagick executable
os.environ['IMAGEMAGICK_BINARY'] = imagemagick_path
change_settings({"IMAGEMAGICK_BINARY": imagemagick_path})

def generate_srt_file(audio_file_path, text_file_path, output_srt_file_path):
    """
    Generates an SRT file using Aeneas from the provided text and audio file paths.
    """
    # Aeneas command to generate SRT
    command = f'python3.10 -m aeneas.tools.execute_task "{audio_file_path}" "{text_file_path}" ' \
              f'"task_language=eng|is_text_type=plain|os_task_file_format=srt" "{output_srt_file_path}"'

    try:
        # Run the command using subprocess
        result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Check for errors in subprocess execution
        if result.returncode == 0:
            logging.info(f'SRT file generated successfully: {output_srt_file_path}')
            return output_srt_file_path  # Return the path of the generated SRT file
        else:
            logging.error(f'Error generating SRT file: {result.stderr.decode("utf-8")}')
            return None
    except Exception as e:
        logging.error(f'An unexpected error occurred while generating SRT file: {e}')
        return None


def convert_text_to_speech(text_file_path, voice_id, api_key, output_audio_file='audio_files'):
    """
    Converts a text file to speech using ElevenLabs and saves the audio in the specified output directory.
    
    Args:
        text_file_path (str): Path to the text file.
        voice_id (str): The voice ID for speech synthesis.
        api_key (str): API key for ElevenLabs authentication.
        output_dir (str): Directory where the output audio file will be saved.
        
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
        audio_data = client.generate(
            text=text,
            voice=Voice(
                voice_id=voice_id,
                settings=VoiceSettings(stability=0.71, similarity_boost=0.5, style=0.0, use_speaker_boost=True)
            )
        )

        # Define the output path for the audio file
         
        
        # Save the generated audio to a file
        os.makedirs(os.path.dirname(output_audio_file), exist_ok=True)
        with open(output_audio_file, 'wb') as audio_file:
            audio_file.write(audio_data)

        logging.info(f"Audio file saved successfully: {output_audio_file}")
        return output_audio_file  # Return the path to the saved audio file

    except FileNotFoundError:
        logging.error("Error: The specified text file was not found.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    
    return None  # Return None if an error occurred





def main():
    if len(sys.argv) != 8:
        print("Usage: python process_video.py <text_file_path> <video_paths_str> <output_video_path> <voice_id> <api_key> <base_path> <textfile_id>")
        sys.exit(1)

    text_file = sys.argv[1]
    video_paths_str = sys.argv[2]
    output_video_path = sys.argv[3]
    voice_id = sys.argv[4]
    api_key = sys.argv[5]
    base_path = sys.argv[6]
    textfile_id = sys.argv[7]

    # Convert video_paths_str back to Python objects
    # video_paths = json.loads(video_paths_str)

    # Example: Read the text file
    with open(text_file, 'r') as file:
        text = file.read()
    
    # video_paths = json.loads(video_paths_str)

    # # Now you have all the data to process with MoviePy and Aeneas
    # # Example: Access the first video clip path
    # for video_clip in video_paths:
    #     line_number = video_clip['line_number']
    #     video_path = video_clip['video_path']
    #     timestamp_start = video_clip['timestamp_start']
    #     timestamp_end = video_clip['timestamp_end']
    # print(f"Video paths string received: {video_paths_str}")

    # try:
    #     video_paths = json.loads(video_paths_str)
    # except json.JSONDecodeError as e:
    #     print(f"Error decoding JSON: {e}")
    #     return


        # Process each video clip here (add logic for MoviePy/Aeneas)
    output_audio_file=os.path.join(base_path,f'{textfile_id}_converted_audio.mp3')
    audio_file = convert_text_to_speech(text_file, voice_id, api_key,output_audio_file)
    logging.info('done with audio file ')
    # Save the final video at output_video path
    output_srt_file_path = os.path.join(base_path, 'srt_files', f'{textfile_id}_generated_srt_output.srt')
    srt_file_path = generate_srt_file(audio_file, text_file, output_srt_file_path)


    # # Read and parse the output file
    # with open(srt_file_path, 'r') as f:
    #     sync_map = json.load(f)
    # # Additional processing with Aeneas or any other operations
    # # ...
    # print(sync_map)

    
if __name__ == "__main__":
    main()
