import json
import threading
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib import messages

from mainapps.audio.models import BackgroundMusic
from mainapps.vidoe_text.color_converter import convert_color_input_to_normalized_rgb
from mainapps.vidoe_text.decorators import check_credits_and_ownership, check_user_credits
from .models import TextFile
import subprocess
import os
import uuid
from django.http import HttpResponse, JsonResponse, Http404
from django.conf import settings
from .models import TextFile, TextLineVideoClip
from threading import Timer
from django.urls import reverse

from django.http import StreamingHttpResponse, Http404
import os
from wsgiref.util import FileWrapper
from django.conf import settings
from django.http import FileResponse, Http404
import requests
from django.contrib.auth.decorators import login_required
from django.core.management import call_command
import io
from django.core.files.base import ContentFile
from mainapps.accounts.models import Credit,VlcPlan

def is_api_key_valid(api_key,voice_id):
    """
    Checks if the given ElevenLabs API key is valid.

    Args:
        api_key (str): The ElevenLabs API key to check.

    Returns:
        bool: True if the API key is valid, False otherwise.
    """
    endpoint_url = f"https://api.elevenlabs.io/v1/voices"
    endpoint_url_2 = f"https://api.elevenlabs.io/v1/voices/{voice_id}"
   
    headers = {
      "Accept": "application/json",
      "xi-api-key": api_key,
      "Content-Type": "application/json"
    }
    x,y=False,False
    try:
        response = requests.get(endpoint_url, headers=headers)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx and 5xx)
        # Check p response content or status code to determine validity
        if response.status_code == 200:
            x=True
            
            
    except requests.RequestException as e:
        print(f"Error checking API key: {e}")
    try:
        response_2 = requests.get(endpoint_url_2,headers=headers)
        if response_2.status_code ==200:
            y=True
    
    except requests.RequestException as e:
        print(f"Error checking API key: {e}")
        
    return x,y


def convert_to_seconds(time_str):
    try:
        minutes, seconds = map(float, time_str.split(':'))
        return minutes * 60 + seconds
    except ValueError:
        return 0.0  # Return 0 or handle error as needed


def format_seconds_to_mm_ss(seconds):
    """Convert seconds to mm:ss format."""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02}:{secs:02}"



def serve_file(request, file_name):
    file_path = os.path.join(settings.MEDIA_ROOT, file_name)

    if not os.path.exists(file_path):
        raise Http404("File does not exist")

    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response

@check_credits_and_ownership(textfile_id_param='textfile_id', credits_required=1)
@login_required  
def process_background_music(request, textfile_id):
    
    # Run process_video command in a new thread
    def run_process_command(textfile_id):
        try:
            call_command('music_processor', textfile_id)
        except Exception as e:
            # Handle the exception as needed (e.g., log it)
            print(f"Error processing video: {e}")

    
    
    textfile = TextFile.objects.get(pk=textfile_id)
    

    if request.method == 'POST':
        if textfile.background_musics:
            for bg in BackgroundMusic.objects.filter(text_file=textfile):
                bg.delete()
        try:
            # Fetch the TextFile instance
            if textfile.user != request.user:
                messages.error(request,'You Do Not have access to the Resources You Requested ')

                return render(request,'permission_denied.html')
        except TextFile.DoesNotExist:
            return Http404("Text file not found")
        no_of_mp3 = int(request.POST.get('no_of_mp3', 0))  # Number of MP3 files
    
        # Check if the necessary fields are present in TextFile
        if not textfile.text_file:
            return JsonResponse({"error": "Text file is missing."}, status=400)
        music_files = [request.FILES.get(f'bg_music_{i}') for i in range(1, no_of_mp3 +1)]  # Adjust based on your inputs
        start_times_str = {f'bg_music_{i}': request.POST.get(f'from_when_{i}') for i in range(1, no_of_mp3 +1)}
        end_times_str = {f'bg_music_{i}': request.POST.get(f'to_when_{i}') for i in range(1, no_of_mp3+1)}
        start_times = [convert_to_seconds(time_str) for time_str in start_times_str.values()]
        end_times = [convert_to_seconds(time_str) for time_str in end_times_str.values()]

        # Save music files and their paths
        music_paths = []
        bg_musics=[]
        for i, music_file in enumerate(music_files, start=1):
            if music_file:
                bg_music=BackgroundMusic(
                        text_file=textfile,
                        music=music_file,
                        start_time=start_times[i-1],
                        end_time=end_times[i-1],
                    )
                
                bg_musics.append(bg_music)
                # Perform bulk creation
        if bg_musics:
            BackgroundMusic.objects.bulk_create(bg_musics)

        lines = []
        for bg_music in bg_musics:
            start_time_str = bg_music.start_time
            end_time_str = bg_music.end_time
            lines.append(f"{bg_music.music.name} {start_time_str} {end_time_str}")

        content = "\n".join(lines)
        
        # Save the content to a text file
        file_name = f'background_music_info_{textfile_id}_.txt'

        textfile.bg_music_text.save(file_name, ContentFile(content))


        try:
            # call_command('music_processor', textfile_id)
            # # Start the background process/
            thread = threading.Thread(target=run_process_command, args=(textfile_id,))
            thread.start()
            return redirect(f'/text/progress_page/bg_music/{textfile_id}')


        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return render(request,'vlc/add_music.html',{'textfile_id':textfile_id,'textfile':textfile})

# @login_required  
# def process_background_music(request, textfile_id):
#     context = {
#         'media_url': settings.MEDIA_URL,
#     }
#     if request.method == 'POST':
#         try:
#             # Fetch the TextFile instance
#             textfile = TextFile.objects.get(pk=textfile_id)
#             if textfile.user != request.user:
#                 messages.error(request,'You Do Not have access to the Resources You Requested ')

#                 return render(request,'permission_denied.html')
#         except TextFile.DoesNotExist:
#             return Http404("Text file not found")
#         no_of_mp3 = int(request.POST.get('no_of_mp3', 0))  # Number of MP3 files
    
#         # Check if the necessary fields are present in TextFile
#         if not textfile.text_file:
#             return JsonResponse({"error": "Text file is missing."}, status=400)
#         music_files = [request.FILES.get(f'bg_music_{i}') for i in range(1, no_of_mp3 +1)]  # Adjust based on your inputs
#         start_times_str = {f'bg_music_{i}': request.POST.get(f'from_when_{i}') for i in range(1, no_of_mp3 +1)}
#         end_times_str = {f'bg_music_{i}': request.POST.get(f'to_when_{i}') for i in range(1, no_of_mp3+1)}
#         start_times = [convert_to_seconds(time_str) for time_str in start_times_str.values()]
#         end_times = [convert_to_seconds(time_str) for time_str in end_times_str.values()]

#         # Save music files and their paths
#         music_paths = []
#         bg_musics=[]
#         for i, music_file in enumerate(music_files, start=1):
#             if music_file:
#                 bg_music=BackgroundMusic(
#                         text_file=textfile,
#                         music_file=music_file,
#                         start_time=start_times[i-1],
#                         end_time=end_times[i-1],
#                     )
                
#                 bg_musics.append(bg_music)
#                 # Perform bulk creation
#         if bg_musics:
#             BackgroundMusic.objects.bulk_create(bg_musics)

#         lines = []
#         for bg_music in bg_musics:
#             start_time_str = bg_music.start_time
#             end_time_str = bg_music.end_time
#             lines.append(f"{bg_music.music_file.name} {start_time_str} {end_time_str}")

#         content = "\n".join(lines)
        
#         # Save the content to a text file
#         file_name = f'background_music_info_{textfile_id}.txt'
#         base_path = settings.MEDIA_ROOT
#         output_video_file_ = os.path.join(base_path, 'final', f"final_output_{textfile_id}.mp4")
        
#         music_info_path = os.path.join(base_path,'bg_music', file_name)  # Adjust path as needed
            
#         if os.path.exists(music_info_path):
#             os.remove(music_info_path)

#         # Create the necessary directories if they do not exist
#         os.makedirs(os.path.dirname(music_info_path), exist_ok=True)
#         with open(music_info_path, 'w') as file:
#             file.write(content)
#         cmd = f'python3.10 music_processor.py "{output_video_file_}" "{music_info_path}" "{str(textfile_id)}" "{base_path}"'
#         process = subprocess.Popen(cmd, shell=True)




#         return redirect(reverse('video:add_scenes', args=[textfile_id]))

#     return render(request,'vlc/add_music.html',{'textfile_id':textfile_id})

# @login_required  
# def process_background_music(request, textfile_id):
#     context = {
#         'media_url': settings.MEDIA_URL,
#     }
#     if request.method == 'POST':
#         try:
#             # Fetch the TextFile instance
#             textfile = TextFile.objects.get(pk=textfile_id)
#             if textfile.user != request.user:
#                 messages.error(request,'You Do Not have access to the Resources You Requested ')

#                 return render(request,'permission_denied.html')
#         except TextFile.DoesNotExist:
#             return Http404("Text file not found")
#         no_of_mp3 = int(request.POST.get('no_of_mp3', 0))  # Number of MP3 files
    
#         # Check if the necessary fields are present in TextFile
#         if not textfile.text_file:
#             return JsonResponse({"error": "Text file is missing."}, status=400)
#         music_files = [request.FILES.get(f'bg_music_{i}') for i in range(1, no_of_mp3 +1)]  # Adjust based on your inputs
#         start_times_str = {f'bg_music_{i}': request.POST.get(f'from_when_{i}') for i in range(1, no_of_mp3 +1)}
#         end_times_str = {f'bg_music_{i}': request.POST.get(f'to_when_{i}') for i in range(1, no_of_mp3+1)}
#         start_times = [convert_to_seconds(time_str) for time_str in start_times_str.values()]
#         end_times = [convert_to_seconds(time_str) for time_str in end_times_str.values()]

#         # Save music files and their paths
#         music_paths = []
#         bg_musics=[]
#         for i, music_file in enumerate(music_files, start=1):
#             if music_file:
#                 bg_music=BackgroundMusic(
#                         text_file=textfile,
#                         music_file=music_file,
#                         start_time=start_times[i-1],
#                         end_time=end_times[i-1],
#                     )
                
#                 bg_musics.append(bg_music)
#                 # Perform bulk creation
#         if bg_musics:
#             BackgroundMusic.objects.bulk_create(bg_musics)

#         lines = []
#         for bg_music in bg_musics:
#             start_time_str = bg_music.start_time
#             end_time_str = bg_music.end_time
#             lines.append(f"{bg_music.music_file.name} {start_time_str} {end_time_str}")

#         content = "\n".join(lines)
        
#         # Save the content to a text file
#         file_name = f'background_music_info_{textfile_id}.txt'
#         base_path = settings.MEDIA_ROOT
#         output_video_file_ = os.path.join(base_path, 'final', f"final_output_{textfile_id}.mp4")
        
#         music_info_path = os.path.join(base_path,'bg_music', file_name)  # Adjust path as needed
            
#         if os.path.exists(music_info_path):
#             os.remove(music_info_path)

#         # Create the necessary directories if they do not exist
#         os.makedirs(os.path.dirname(music_info_path), exist_ok=True)
#         with open(music_info_path, 'w') as file:
#             file.write(content)
#         cmd = f'python3.10 music_processor.py "{output_video_file_}" "{music_info_path}" "{str(textfile_id)}" "{base_path}"'
#         process = subprocess.Popen(cmd, shell=True)




#         return redirect(reverse('video:add_scenes', args=[textfile_id]))

#     return render(request,'vlc/add_music.html',{'textfile_id':textfile_id})

def clean_progress_file(text_file_id):
    """Deletes the progress file after 3 seconds when progress is 100%."""
    if os.path.exists(f'{settings.MEDIA_ROOT}/{text_file_id}_progress.txt'):
        os.remove(f'{settings.MEDIA_ROOT}/{text_file_id}_progress.txt')

def progress(request,text_file_id):
        text_file=TextFile.objects.get(id=text_file_id)
    
        return JsonResponse({'progress': text_file.progress})

@login_required
def progress_page(request,al_the_way,text_file_id):

    return render(request,'vlc/progress.html',{"al_the_way":al_the_way,'text_file_id':text_file_id})

@check_credits_and_ownership(textfile_id_param='textfile_id', credits_required=1)
@login_required
def process_textfile(request, textfile_id):
    try:
        # Fetch the TextFile instance
        textfile = TextFile.objects.get(pk=textfile_id)
        if textfile.user != request.user:
            messages.error(request, 'You do not have access to the resources you requested.')
            return render(request, 'permission_denied.html')
    except TextFile.DoesNotExist:
        raise Http404("Text file not found")

    if not textfile_id:
        return JsonResponse({'error': 'text_file_id is required.'}, status=400)

    # Run process_video command in a new thread
    def run_process_command(textfile_id):
        try:
            call_command('process_video', textfile_id)
        except Exception as e:
            # Handle the exception as needed (e.g., log it)
            print(f"Error processing video: {e}")

    # Start the background process
    thread = threading.Thread(target=run_process_command, args=(textfile_id,))
    thread.start()

    # Redirect to another page while the process runs in the background
    return redirect(f'/text/progress_page/build/{textfile_id}')


# def process_textfile(request, textfile_id):
#     try:
#         # Fetch the TextFile instance
#         textfile = TextFile.objects.get(pk=textfile_id)
#         if textfile.user != request.user:
#             messages.error(request,'You Do Not have access to the Resources You Requested ')

#             return render(request,'permission_denied.html')
#     except TextFile.DoesNotExist:
#         return Http404("Text file not found")

#     if not textfile_id:
#         return JsonResponse({'error': 'text_file_id is required.'}, status=400)

#     try:
#         call_command('process_video', textfile_id)
#         return redirect(f'/text/progress_page/build/{textfile_id}')

#     except Exception as e:
#         return JsonResponse({'error': str(e)}, status=500)



# @login_required
# def process_textfile(request, textfile_id):
#     try:
#         # Fetch the TextFile instance
#         textfile = TextFile.objects.get(pk=textfile_id)
#         if textfile.user != request.user:
#             messages.error(request,'You Do Not have access to the Resources You Requested ')

#             return render(request,'permission_denied.html')

#     except TextFile.DoesNotExist:
#         return Http404("Text file not found")

#     # Check if the necessary fields are present in TextFile
#     if not textfile.text_file:
#         return JsonResponse({"error": "Text file is missing."}, status=400)
#     # base_path = os.path.join(os.getcwd(),'media')

#     # Prepare paths for video and output files
#     base_path = settings.MEDIA_ROOT
#     output_video_path = os.path.join(base_path, 'videos', f"{textfile_id}_output.mp4")

#     # Gather all TextLineVideoClip instances for this TextFile
#     video_clips = textfile.video_clips.all().order_by('line_number')
#     if not video_clips.exists():
#         return JsonResponse({"error": "No video clips found for this TextFile."}, status=400)

#     # Create a mapping of line numbers to their respective video paths or default to a placeholder
#     video_paths = []
#     for clip in video_clips:
#         if clip.video_file:
#             video_path=clip.video_file
#         else:
#             video_path = clip.video_file_path if clip.video_file_path else ''  # Fallback to empty string if not available

#         video_paths.append({
#             "line_number": clip.line_number,
#             "video_path": video_path,
#             "timestamp_start": clip.timestamp_start,
#             "timestamp_end": clip.timestamp_end
#         })
#     video_clips_dict = [clip.to_dict() for clip in video_clips]
#     # video_clips_json = json.dumps(video_clips_dict)
#     # Convert video_paths to a string for passing to the script
#     video_paths_str = str(video_paths)

#     json_file_path =f'{base_path}/tmp/{textfile_id}/video_clips.json'
#     # Check if the output file already exists and delete it
#     if os.path.exists(json_file_path):
#         os.remove(json_file_path)

#     # Create the necessary directories if they do not exist
#     os.makedirs(os.path.dirname(json_file_path), exist_ok=True)
#     # text_file_dir=os.path.join(base_path,textfile.text_file.name)
#     # os.makedirs(os.path.dirname(text_file_dir), exist_ok=True)

#     # with open(text_file_dir,'w') as f:
#     #     f.write(textfile.text_file)
#     # Write the serialized data to a JSON file
#     with open(json_file_path, 'w') as f:
#         json.dump(video_clips_dict, f)
#         # f.write(str(video_clips_dict))
#     resolution=textfile.resolution
#     # Prepare the command to call the external script (e.g., MoviePy and Aeneas processing)
#     command = [
#         'python3.10', 'process_video.py',
#         textfile.text_file.path,
#         json_file_path,       # Pass video paths mapping
#         output_video_path,     # Path for the output video
#         textfile.voice_id,     # Pass the voice_id
#         textfile.api_key  ,     # Pass the api_key
#         base_path,
#         textfile_id,
#         resolution,
#         textfile.font_color,
#         textfile.subtitle_box_color,
#         textfile.font_file.path,
#         str(textfile.font_size),
        
#     ]

#     # Start the subprocess
#     try:
#         subprocess.Popen(command,)  # Run it asynchronously
#     except Exception as e:
#         return JsonResponse({"error": f"Error running subprocess: {str(e)}"}, status=500)

#     # Return success message
#     return redirect(f'/text/progress_page/build/{textfile_id}')

@check_user_credits(minimum_credits_required=1)
@login_required
def add_text(request):
    if request.method == 'POST':
        voice_id = request.POST.get('voiceid')
        api_key = request.POST.get('elevenlabs_apikey')
        resolution = request.POST.get('resolution')
        font_color = request.POST.get('font_color')
        subtitle_box_color = request.POST.get('subtitle_box_color')
        font_file = request.FILES.get('font_file')  # Assuming this is a different file field
        font_size = request.POST.get('font_size')
        x,y= is_api_key_valid(api_key,voice_id)
        if x and y:
                
            if  voice_id and api_key:
                text_obj=TextFile.objects.create(
                    user=request.user,

                    voice_id=voice_id,
                    api_key=api_key,
                    resolution=resolution,
                    font_file=font_file,
                    subtitle_box_color=subtitle_box_color,
                    font_size=font_size,
                    font_color=font_color
                )
                return redirect(reverse('video:add_scenes', args=[text_obj.id]))

            else:
                messages.error(request,'Please provide all required fields.')
                return render(request, 'vlc/frontend/VLSMaker/index.html', {
                    'error': 'Please provide all required fields.'
                })
        elif x and not y:
            messages.error(request,'The voice ID you provided is invalid, please provide a valid one')
            return render(request, 'vlc/frontend/VLSMaker/index.html', {
                'error': 'Please provide valid API key'
            })
        elif not x:
            messages.error(request,'The API key you provided is invalid, please provide a valid one!')
            return render(request, 'vlc/frontend/VLSMaker/index.html', {
                'error': 'Please provide valid API key'
            })
        
    return render(request, 'vlc/frontend/VLSMaker/index.html')

# @login_required
# def add_text_file(request, textfile_id):
#     text_file_present=False
#     text_file_obj= get_object_or_404(TextFile,id=textfile_id)
#     return render(request,'vlc/frontend/VLSMaker/index.html',{"textfile_id":textfile_id,})

@check_credits_and_ownership(textfile_id_param='textfile_id', credits_required=1)
@login_required
def download_video(request,textfile_id,):
    text_file=TextFile.objects.get(id=textfile_id)
    user_credit, created = Credit.objects.get_or_create(user=request.user)
    user_credit.credits-=1
    user_credit.save()

    bg_music=request.GET.get('bg_music',None)
    return render(request,'vlc/download.html',{'textfile_id':textfile_id,'bg_music':bg_music,'text_file':text_file}, )
