from django.shortcuts import render, redirect
from .models import TextFile
import subprocess
import os
import uuid
from django.http import JsonResponse, Http404
from django.conf import settings
from .models import TextFile, TextLineVideoClip
def process_textfile(request, textfile_id):
    try:
        # Fetch the TextFile instance
        textfile = TextFile.objects.get(pk=textfile_id)
    except TextFile.DoesNotExist:
        return Http404("Text file not found")

    # Check if the necessary fields are present in TextFile
    if not textfile.text_file:
        return JsonResponse({"error": "Text file is missing."}, status=400)

    # Prepare paths for video and output files
    base_path = settings.MEDIA_ROOT
    output_video_path = os.path.join(base_path, 'videos', f"{textfile_id}_output.mp4")

    # Gather all TextLineVideoClip instances for this TextFile
    video_clips = textfile.video_clips.all().order_by('line_number')
    if not video_clips.exists():
        return JsonResponse({"error": "No video clips found for this TextFile."}, status=400)

    # Create a mapping of line numbers to their respective video paths or default to a placeholder
    video_paths = []
    for clip in video_clips:
        video_path = clip.video_file_path if clip.video_file_path else ''  # Fallback to empty string if not available
        video_paths.append({
            'line_number': clip.line_number,
            'video_path': video_path,
            'timestamp_start': clip.timestamp_start,
            'timestamp_end': clip.timestamp_end
        })

    # Convert video_paths to a string for passing to the script
    video_paths_str = str(video_paths)

    # Prepare the command to call the external script (e.g., MoviePy and Aeneas processing)
    command = [
        'python3.10', 'process_video.py',
        textfile.text_file.path,
        video_paths_str,       # Pass video paths mapping
        output_video_path,     # Path for the output video
        textfile.voice_id,     # Pass the voice_id
        textfile.api_key  ,     # Pass the api_key
        base_path,
        textfile_id,
    ]

    # Start the subprocess
    try:
        subprocess.Popen(command)  # Run it asynchronously
    except Exception as e:
        return JsonResponse({"error": f"Error running subprocess: {str(e)}"}, status=500)

    # Return success message
    return JsonResponse({'status': 'Processing started', 'textfile_id': textfile_id, 'output_video': output_video_path})

def add_text(request):
    if request.method == 'POST':
        textfile = request.FILES.get('textfile')
        voice_id = request.POST.get('voiceid')
        api_key = request.POST.get('elevenlabs_apikey')
        resolution = request.POST.get('resolution')
        font_color = request.POST.get('font_color')
        subtitle_box_color = request.POST.get('subtitle_box_color')
        font_file = request.FILES.get('font_file')  # Assuming this is a different file field
        font_size = request.POST.get('font_size')

        if textfile and voice_id and api_key:
            text_obj=TextFile.objects.create(
                text_file=textfile,
                voice_id=voice_id,
                api_key=api_key,
                resolution=resolution,
                font_file=font_file,
                subtitle_box_color=subtitle_box_color,
                font_size=font_size,
                font_color=font_color
            )
            return redirect(f'/video/add-scene/{text_obj.id}')  # Redirect to a success page or another URL
        else:
            return render(request, 'vlc/frontend/VLSMaker/index.html', {
                'error': 'Please provide all required fields.'
            })
    return render(request, 'vlc/frontend/VLSMaker/index.html')
