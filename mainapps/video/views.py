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
                folder_name = folder_name.replace(' ', '_')
                category, created = ClipCategory.objects.get_or_create(
                    name=folder_name, parent=parent, user=request.user
                )
                parent = category  # Make the current folder the parent for the next iteration

            # Now save the files under the last category (deepest folder)
            for file_name in files:
                file = next(f for f in uploaded_folder if f.name == file_name)
                VideoClip.objects.create(
                    title=file_name,
                    video_file=file,
                    category=parent
                )

        return redirect('/text')  # Redirect to a success page or some other view

    return render(request, 'upload.html')

# @login_required
# def upload_video_folder(request):
#     if request.method == 'POST':
#         uploaded_folder = request.FILES.getlist('folder')  # Get all files from the uploaded folder

#         # Process each uploaded file
#         for file in uploaded_folder:
#             folder_path = Path(file.name).parent.parts  # Extract the folder structure, ignoring the file name
#             parent = None
#             print('folder_path: ', folder_path)

#             # Create each folder/subfolder as a category
#             for folder_name in folder_path:
#                 folder_name = folder_name.replace(' ', '_')  # Replace spaces with underscores
#                 print(f"Processing folder: {folder_name}")

#                 # Get or create the category for this folder
#                 category, created = ClipCategory.objects.get_or_create(
#                     name=folder_name, parent=parent, user=request.user
#                 )
                
#                 # Log whether the category was created or already existed
#                 if created:
#                     print(f"Created new category: {category.name}")
#                 else:
#                     print(f"Category {category.name} already exists")
                
#                 # Set the current category as the parent for the next folder in the hierarchy
#                 parent = category

#             # Once all folders are processed, save the video file in the deepest category
#             video_title = os.path.basename(file.name)  # Extract file name for video title
#             VideoClip.objects.create(title=video_title, video_file=file, category=parent)

#         return redirect('/text')  # Redirect to a success page or another view

#     return render(request, 'upload.html')




@login_required
def add_video_clips(request, textfile_id):
    text_file = get_object_or_404(TextFile, id=textfile_id)

    video_categories=ClipCategory.objects.all()
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
                    return redirect(f'/video/add-scene/{textfile_id}')


            TextLineVideoClip.objects.bulk_create(video_clips_data)
            return redirect(f'/text/process-textfile/{textfile_id}')  # Redirect to a success page or another appropriate view

        elif request.POST.get('purpose') == 'text_file':
            if request.FILES.get('text_file'):
                text_file.text_file=request.FILES.get('text_file')
                text_file.save()
                return redirect(f'/video/add-scene/{textfile_id}')
            messages.error(request,'You did not upload text file')
            return redirect(f'/video/add-scene/{textfile_id}')


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