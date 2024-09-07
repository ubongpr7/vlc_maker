from django.shortcuts import render, redirect
from .models import TextFile

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
            TextFile.objects.create(
                text_file=textfile,
                voice_id=voice_id,
                api_key=api_key,
                resolution=resolution,
                font_file=font_file,
                subtitle_box_color=subtitle_box_color,
                font_size=font_size,
                font_color=font_color
            )
            return redirect('/')  # Redirect to a success page or another URL
        else:
            return render(request, 'vlc/frontend/VLSMaker/index.html', {
                'error': 'Please provide all required fields.'
            })
    return render(request, 'vlc/frontend/VLSMaker/index.html')
