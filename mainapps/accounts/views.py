from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout, get_user_model
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from mainapps.accounts.emails import send_html_email2, welcome_message
from mainapps.accounts.models import Credit
import stripe
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator, PasswordResetTokenGenerator
from djstripe.settings import djstripe_settings
from django.conf import settings
from django.urls import reverse, reverse_lazy
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt
from djstripe.models import Subscription, Customer, Product, APIKey, Plan
from django.utils.timezone import now
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import views as auth_views

@csrf_exempt  
def contact_view(request):
    if request.method == 'POST':
        # Extract the data from the request
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Prepare the email content
        subject = f"New Contact Form Submission from {first_name} {last_name}"
        email_body = f"First Name: {first_name}\nLast Name: {last_name}\nEmail: {email}\nMessage:\n{message}"

        # Send the email to the support team
        try:
            send_mail(subject, email_body, settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_FROM_EMAIL,])  # Replace with your support email
            return JsonResponse({'success': True, 'message': 'Your message has been sent successfully!'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})


def logout_view(request):
    """
    Logs out the user and redirects to the login page or homepage.
    """
    # Log the user out
    logout(request)
    
    # Add a success message
    messages.success(request, "You Have Been Successfully Logged Out.")
    
    # Redirect to the login page or homepage
    return redirect('/')  # Replace 'login' with the name of the URL to redirect to (e.g., 'home' or 'login')



def login(request):
    if request.user.is_authenticated:
        return redirect('/text')
    
    if request.method == 'POST':
        # Get username and password from the form
        username = request.POST['username']
        password = request.POST['password']
        
        # Authenticate the user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # If the user exists, log them in
            auth_login(request, user)  # Note: Using `auth_login` here to avoid conflict
            messages.success(request, 'Successfully Logged In!')
            try:
                return redirect(request.session.get('next'))  
            except:
                return redirect('/text')  

        else:
            # If login failed, send an error message
            messages.error(request, 'Invalid Username or Password. Please Try Again.')
    next=request.GET.get('next','')
    request.session['next']=next
    return render(request,'accounts/login.html',)


@require_POST
def payment_method(request):
    plan =request.POST.get('plan')
    automatic =request.POST.get('automatic')
    payment_meth =request.POST.get('payment_method')





def embedded_pricing_page(request):
    return render(request, 'accounts/embed_stripe.html', 
    #     {
    #     'stripe_public_key': djstripe_settings.STRIPE_PUBLIC_KEY,
    #     'stripe_pricing_table_id': settings.STRIPE_PRICING_TABLE_ID,
    # }
    )





@csrf_exempt
def stripe_webhook(request):
    # Get the Stripe API key from the dj-stripe APIKey model
    stripe_api_key = APIKey.objects.filter(livemode=True,type="secret").first()
    stripe.api_key = stripe_api_key.secret if stripe_api_key else None
    
    # Proceed only if the API key is found
    if not stripe.api_key:
        return HttpResponse("Stripe API key not found", status=500)

    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    endpoint_secret = stripe_api_key.djstripe_owner_account.webhook_secret  # Assuming webhook secret is stored in the account model

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return HttpResponse(status=400)

    # Handle the checkout.session.completed event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        customer_email = session['customer_details']['email']
        subscription_id = session['subscription']

        # Implement user creation and subscription processing here

    return HttpResponse(status=200)

def subscription_confirm(request):
    stripe_api_key = APIKey.objects.filter(livemode=False, type="secret").first()
    if not stripe_api_key:
        messages.error(request, "Stripe API key Not Found.")
        return HttpResponseRedirect(reverse("home:home"))

    stripe.api_key = str(stripe_api_key.secret)

    session_id = request.GET.get("session_id")
    if not session_id:
        messages.error(request, "Session ID Is Missing.")
        return HttpResponseRedirect(reverse("home:home"))

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        customer_email = session.customer_details.email
        subscription_id = session.subscription
        customer_name = session.customer_details.name
        stripe_customer = stripe.Customer.retrieve(session.customer)

        # Extract names
        first_name = customer_name.split()[0] if customer_name else ""
        last_name = " ".join(customer_name.split()[1:]) if customer_name and len(customer_name.split()) > 1 else ""

        # Retrieve subscription and product
        subscription = stripe.Subscription.retrieve(subscription_id)
        stripe_product_id = subscription["items"]["data"][0]["plan"]["product"]

        # Set product credits
        product_credits = {
            "prod_QsWVUlHaCH4fqL": 25,
            "prod_QsWWDNjdR6j22q": 50,
            "prod_QsWWaDzX83oGhP": 100,
            "prod_QrRbiNv4BrEp4L": 25,
            "prod_QrRcSTxkwx207Z": 50,
            "prod_QrRcGMHuLrp4Lz": 100,
        }
        credits = product_credits.get(stripe_product_id, 0)

        # Save necessary information in session
        request.session['stripe_customer_email'] = customer_email
        request.session['first_name'] = first_name
        request.session['last_name'] = last_name
        request.session['stripe_product_id'] = stripe_product_id
        request.session['credits'] = credits

        # Redirect to registration page
        return HttpResponseRedirect(reverse('accounts:registration'))

    except stripe.error.StripeError as e:
        messages.error(request, f"Stripe error: {e}")
        return HttpResponseRedirect(reverse("home:home"))

    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {e}")
        return HttpResponseRedirect(reverse("home:home"))

def welcome(request,id):
    User = get_user_model()
    
    user=User.objects.get(id=id)
    context = {
            'user_name': user.first_name,
        }

    send_html_email2(
        subject="Welcome to VideoCrafter.io – Let’s Create Some Amazing Creatives!",
        message=None,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_email=user.email,
        html_file='accounts/welcome.html',  # Path to your HTML email template
        context=context
    )
    return HttpResponseRedirect(reverse("video_text:add_text")) 
    
    

def registration_view(request):
    stripe_product_id = request.session.get('stripe_product_id')
    if not stripe_product_id:
        messages.info(request,'You Need To Subscribe To Register')
        return redirect('/accounts/pricing')

    product_credits = {
            "prod_QsWVUlHaCH4fqL": 25,
            "prod_QsWWDNjdR6j22q": 50,
            "prod_QsWWaDzX83oGhP": 100,
            "prod_QrRbiNv4BrEp4L": 25,
            "prod_QrRcSTxkwx207Z": 50,
            "prod_QrRcGMHuLrp4Lz": 100,
        }
    if request.method == 'POST':
        # Get data from HTML form
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        # Basic validation for passwords
        if len(password1) <6:
            messages.error(request, "At Least 6 Characters Are Required")
            return HttpResponseRedirect(reverse("accounts:registration")) 

        if password1 != password2:
            messages.error(request, "Passwords Do Not Match.")
            return HttpResponseRedirect(reverse("accounts:registration")) 

        # Check if the email is already registered
        
        User = get_user_model()
        if User.objects.filter(email=email).exists():
            messages.error(request, "This Email Is Already Registered.")
            return HttpResponseRedirect(reverse("accounts:registration")) 

        # Create a new user
        user = User.objects.create_user(email=email, password=password1)

        # Fetch Stripe details from the session
        first_name = request.session.get('first_name', '')
        last_name = request.session.get('last_name', '')

        # Set first and last name from session
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        # welcome_message(user)
        

        try:
            djstripe_product = Product.objects.get(id=stripe_product_id)
            Credit.create_or_update_credit(user=user, product=djstripe_product, credits=product_credits.get(stripe_product_id, 0))
        except Product.DoesNotExist:
            messages.error(request, "Product not found.")
            return HttpResponseRedirect(reverse("home:home"))  # Update with correct view name

        # Log the user in
        auth_login(request, user)
        messages.success(request, "Account Created Successfully!")
        return redirect(f"/accounts/welcome/{user.pk}")

    else:
        # Handle GET request (render the registration form)
        return render(request, 'accounts/register.html')  # Update with your actual registration template

def subscription_details(request):
    user = request.user
    customer = Customer.objects.filter(subscriber=user).first()
    
    if customer:
        # Get the active subscription for the customer
        subscription = Subscription.objects.filter(customer=customer, status="active").first()
        
        if subscription:
            current_plan = subscription.plan
            all_plans = Plan.objects.filter(active=True).exclude(id=current_plan.id)  # Get all other active plans
            
            context = {
                'subscription': subscription,
                'current_plan': current_plan,
                'all_plans': all_plans
            }
            return render(request, 'subscription/details.html', context)
    
    return render(request, 'accounts/details.html')  # In case the user has no subscription


