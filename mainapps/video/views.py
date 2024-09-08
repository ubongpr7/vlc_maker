from django.shortcuts import render, redirect, get_object_or_404
from mainapps.vidoe_text.models import TextFile, TextLineVideoClip
from django.http import HttpResponse
from django.forms import modelformset_factory
from django.views.decorators.csrf import csrf_exempt
from .models import VideoClip,ClipCategory

@csrf_exempt
def add_video_clips(request, textfile_id):
    text_file = get_object_or_404(TextFile, id=textfile_id)
    video_categories=ClipCategory.objects.all()
    if request.method == 'POST':
        lines = text_file.process_text_file()
        video_clips_data = []

        for index, line in enumerate(lines):
            video_file = request.FILES.get(f'video_file_{index}')
            timestamp_start = request.POST.get(f'timestamp_start_{index}')
            timestamp_end = request.POST.get(f'timestamp_end_{index}')
            
            if video_file:
                video_clips_data.append(
                    TextLineVideoClip(
                        text_file=text_file,
                        video_file_path=video_file,
                        line_number=index + 1,
                        timestamp_start=timestamp_start,
                        timestamp_end=timestamp_end
                    )
                )


        TextLineVideoClip.objects.bulk_create(video_clips_data)
        return redirect('/')  # Redirect to a success page or another appropriate view
    

    else:
        lines = text_file.process_text_file()
        # Create a list of dictionaries with line numbers for the form
        form_data = [{'line_number': i + 1,'line':lines[i],'i':i} for i in range(len(lines))]
        return render(request, 'vlc/frontend/VLSMaker/sceneselection/index.html', {'text_file': text_file,'video_categories':video_categories, 'form_data': form_data})

def get_clip(request,cat_id):
    category=get_object_or_404(ClipCategory,id=cat_id)
    videos=VideoClip.objects.filter(category=category)
    return render(request,'partials/model_options.html', {'items':videos})