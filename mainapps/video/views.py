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
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt



# views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse


def rename_video_clip(request, video_id):
    video_clip = get_object_or_404(VideoClip, id=video_id)
    if request.method == 'POST':
        new_title = request.POST.get('newName')
        video_clip.title = new_title
        video_clip.save()
        return JsonResponse({'success': True})
    return render(request, 'rename.html', {'item': video_clip})

def rename_folder(request, category_id):
    folder = get_object_or_404(ClipCategory, id=category_id)
    if request.method == 'POST':
        new_name = request.POST.get('newName')
        folder.name = new_name
        folder.save()
        return JsonResponse({'success': True})
    return render(request, 'rename.html', {'item': folder})

# views.py
@login_required
def add_video_clip(request, category_id):
    category = get_object_or_404(ClipCategory, id=category_id)

    if request.method == 'POST':
        # Handle the form submission
        video_file = request.FILES.get('video_file')
        title=request.POST.get('title')
        if video_file:
            clip = VideoClip.objects.create(video_file=video_file, title=title,category=category)
            clip.save()
            return HttpResponse(status=204)  # Return no content for successful POST
        
    return render(request, 'partials/add_video.html', {'category': category})


@login_required
def delete_clip(request, clip_id):
    clip = get_object_or_404(VideoClip, id=clip_id)
    if request.method == 'POST':
        # Retrieve the clip or return a 404 if not found

        # Delete the video file from storage (optional)
        if clip.video_file:
            clip.video_file.delete(save=False)

        # Delete the video clip from the database
        clip.delete()

        # Return a success response
        return JsonResponse({'success': True})

    # Return a method not allowed response for non-POST requests

    return render(request,'partials/confirm_delete.html',{'item':clip})

@login_required
def delete_category(request, category_id):
    category = get_object_or_404(ClipCategory, id=category_id)
    if request.method == 'POST':

        # Recursively delete the category, its subcategories, and all related video clips
        def delete_category_and_subcategories(cat):
            # Delete all video clips associated with this category
            cat.video_clips.all().delete()

            # Recursively delete subcategories
            for subcategory in cat.subcategories.all():
                delete_category_and_subcategories(subcategory)

            # Finally, delete the category itself
            cat.delete()

        delete_category_and_subcategories(category)
        
        # Return a success response (JSON or redirect based on your UI)
        return JsonResponse({'success': True})

    # Return a method not allowed response for non-POST requests
    return render(request,'partials/confirm_delete.html',{'item':category})

@login_required
def category_view(request, category_id=None,video_id=None):
    videos =[]
    subcategories=[]
    main_categories=[]
    current_category = None
    video=None
    if category_id:
        # If a category is clicked, fetch the current category and its subcategories and videos
        current_category = get_object_or_404(ClipCategory, id=category_id,user=request.user)
        subcategories = current_category.subcategories.all()
        videos = current_category.video_clips.all()

        if video_id:
            video=VideoClip.objects.get(category=current_category, id=video_id)
    else:
        # If no category_id is provided, display the root categories (categories without a parent)
        main_categories = ClipCategory.objects.filter(user=request.user)

        # videos = VideoClip.objects.filter(category__isnull=True,)

    context = {
        'current_category': current_category,
        'folders': main_categories,
        'subcategories': subcategories,
        'videos': videos,
        'category_id':category_id,
        'video_id':video_id,
        'video':video,
    }
    return render(request, 'assets/assets.html', context)

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

    return render(request, 'dir_upload.html')


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