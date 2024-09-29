from django.shortcuts import redirect, render

# Create your views here.from django.shortcuts import redirect

def home(request):
    if request.user.is_authenticated:
        return redirect('/text')
    else:
        return render(request, 'vlc/frontend/landing.html')




    