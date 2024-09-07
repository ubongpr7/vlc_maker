from django.shortcuts import render

# Create your views here.
def make_video(request):
    return render(request,'vlc/frontend/VLSMaker/index.html')
    