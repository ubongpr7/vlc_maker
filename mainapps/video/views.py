from django.shortcuts import render, redirect, get_object_or_404
from mainapps.vidoe_text.models import TextFile, TextLineVideoClip
from django.http import HttpResponse
from django.forms import modelformset_factory
from django.views.decorators.csrf import csrf_exempt
from .models import VideoClip,ClipCategory
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import os
from django.core.files.storage import FileSystemStorage
from pathlib import Path
import json
from django.urls import reverse


# views.py
from django.shortcuts import render, get_object_or_404

def category_view(request, category_id=None):
    if category_id:
        # If a category is clicked, fetch the current category and its subcategories and videos
        current_category = get_object_or_404(ClipCategory, id=category_id,user=request.user)
        subcategories = current_category.subcategories.all()
        videos = current_category.videos.all()
    else:
        # If no category_id is provided, display the root categories (categories without a parent)
        current_category = None
        subcategories = ClipCategory.objects.filter(parent__isnull=True)
        videos = VideoClip.objects.filter(category__isnull=True)

    context = {
        'current_category': current_category,
        'subcategories': subcategories,
        'videos': videos
    }
    return render(request, 'category_view.html', context)

@login_required
def upload_video_folder(request):
    if request.method == 'POST':
        if 'directories' not in request.POST:
            return render(request, 'upload.html', {'error': 'No directory data provided.'})

        uploaded_folder = request.FILES.getlist('folder')
        directories = json.loads(request.POST['directories'])  # Get folder structure from the frontend

        for folder_path, files in directories.items():
            folder_parts = folder_path.split('/')  # Split folder path into parts (subfolders)
            parent = None

            # Create categories and subcategories based on folder structure
            for folder_name in folder_parts:
                category, created = ClipCategory.objects.get_or_create(
                    name=folder_name, parent=parent, user=request.user
                )
                parent = category  # Make the current folder the parent for the next iteration

            # Now save the files under the last category (deepest folder)
            for file_name in files:
                # Filter uploaded files by name, also ensuring that the file is a valid video type
                file = next((f for f in uploaded_folder if f.name == file_name), None)
                if file:
                    # Check if the file is empty (size == 0 bytes)
                    if file.size != 0:
                    
                    
                        video_extensions = ['mp4', 'webm', 'mkv', 'avi', 'mov']
                        if file.name.split('.')[-1].lower() in video_extensions:
                            VideoClip.objects.create(
                                title=file_name,
                                video_file=file,
                                category=parent
                            )
                        else:
                            # Optionally, handle files that aren't valid video types
                            messages.warning(request, f"File '{file_name}' is not a valid video format.")
                    else:
                        messages.warning(request, f"File '{file_name}' is empty and has been skipped.")

                        continue
                else:
                    continue
        messages.success(request, 'Files uploaded successfully!')
        return HttpResponse('Upload successful!')

    return render(request, 'upload.html')


@login_required
def add_video_clips(request, textfile_id):
    text_file = get_object_or_404(TextFile, id=textfile_id)
    if text_file.user != request.user:
        messages.error(request,'You Do Not have access to the Resources You Requested ')
        return render(request,'permission_denied.html')
    video_categories=ClipCategory.objects.filter(user=request.user)
    if request.method == 'POST':
        if  text_file.text_file and request.POST.get('purpose') == 'process':
            if text_file.video_clips:

                for video_clip in TextLineVideoClip.objects.filter(text_file=text_file):
                    video_clip.delete()
                    print('Deleted a video_clip')
            

            lines = text_file.process_text_file()
            print(lines)
            video_clips_data = []

            for index, line in enumerate(lines):
                video_file = request.FILES.get(f'uploaded_video_{index}')
                video_clip_id = request.POST.get(f'selected_video_{index}')
                # timestamp_start = request.POST.get(f'timestamp_start_{index}')
                # timestamp_end = request.POST.get(f'timestamp_end_{index}')
                if video_clip_id:
                    video_clip= get_object_or_404(VideoClip,id=video_clip_id)
                else:
                    video_clip=None

                if video_file or  video_clip:
                    video_clips_data.append(
                        TextLineVideoClip(
                            text_file=text_file,
                            video_file=video_clip,
                            video_file_path=video_file,
                            line_number=index + 1,
                            # timestamp_start=timestamp_start,
                            # timestamp_end=timestamp_end
                        )
                    )
                else:
                    messages.error(request,"You did not choose the clips completely")
                    return redirect(reverse('video:add_scenes', args=[textfile_id]))
                


            TextLineVideoClip.objects.bulk_create(video_clips_data)
            
            return redirect(f'/text/process-textfile/{textfile_id}')  # Redirect to a success page or another appropriate view

        elif request.POST.get('purpose') == 'text_file':
            if request.FILES.get('text_file'):
                text_file.text_file=request.FILES.get('text_file')
                text_file.save()
                return redirect(reverse('video:add_scenes', args=[textfile_id]))
            
            messages.error(request,'You did not upload text file')
            return redirect(reverse('video:add_scenes', args=[textfile_id]))


    else:
        if text_file.text_file:
            lines = text_file.process_text_file()
            # Create a list of dictionaries with line numbers for the form
            form_data = [{'line_number': i + 1,'line':lines[i],'i':i} for i in range(len(lines))]
            return render(request, 'vlc/frontend/VLSMaker/sceneselection/index.html', {'text_file': text_file,'video_categories':video_categories,'textfile_id':textfile_id, 'form_data': form_data})
        return render(request, 'vlc/frontend/VLSMaker/sceneselection/index.html', {'text_file': text_file,'textfile_id':textfile_id})

def get_clip(request,cat_id):
    category=get_object_or_404(ClipCategory,id=cat_id)
    videos=VideoClip.objects.filter(category=category)
    return render(request,'partials/model_options.html', {'items':videos})