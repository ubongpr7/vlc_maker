from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages

# Create your views here.
def login(request):
    
    if request.method == 'POST':
        # Get username and password from the form
        username = request.POST['username']
        password = request.POST['password']
        
        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # If the user exists, log them in
            login(request, user)
            messages.success(request, 'Successfully logged in!')
            return redirect('/text')  # Redirect to a 'home' page or any other page after login
        else:
            # If login failed, send an error message
            messages.error(request, 'Invalid username or password. Please try again.')
    return render(request,'accounts/login.html',)



