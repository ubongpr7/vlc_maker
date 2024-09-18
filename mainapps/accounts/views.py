from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.views.decorators.http import require_POST

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
            auth_login(request, user)  # Note: Using `auth_login` here to avoid conflict
            messages.success(request, 'Successfully logged in!')
            try:
                return redirect(request.session.get('next'))  
            except:
                return redirect('/text')  

        else:
            # If login failed, send an error message
            messages.error(request, 'Invalid username or password. Please try again.')
    next=request.GET.get('next','')
    request.session['next']=next
    return render(request,'accounts/login.html',)


@require_POST
def payment_method(request):
    plan =request.POST.get('plan')
    automatic =request.POST.get('automatic')
    payment_meth =request.POST.get('payment_method')
