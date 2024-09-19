from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.views.decorators.http import require_POST
from djstripe.settings import djstripe_settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.contrib.auth import get_user_model
import stripe

from django.contrib.auth import get_user_model
from djstripe.models import Subscription, Customer,APIKey
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib import messages
from django.db import IntegrityError
from django.views.decorators.csrf import csrf_exempt

# Set the Stripe secret key
from django.http import HttpResponse




from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

def send_registration_email(user, password, request):
    subject = 'Welcome to Our Platform!'
    from_email = 'no-reply@example.com'
    to = user.email
    
    # Prepare the context for the email template
    context = {
        'user': user,
        'password': password,
        'password_reset_link': request.build_absolute_uri(reverse('password_reset'))
    }
    
    # Render the HTML template
    html_content = render_to_string('partials/regiter_email.html', context)
    text_content = strip_tags(html_content)  # Fallback for plain text email

    # Create the email
    email = EmailMultiAlternatives(subject, text_content, from_email, [to])
    email.attach_alternative(html_content, "text/html")
    
    # Send the email
    email.send()




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


# def subscription_confirm(request):
#     # Get the session ID from the URL
#     session_id = request.GET.get("session_id")
#     if not session_id:
#         messages.error(request, "Session ID is missing.")
#         return HttpResponseRedirect(reverse("subscription_details"))

#     # Retrieve session data from Stripe
#     session = stripe.checkout.Session.retrieve(session_id)

#     # Extract customer email from the session
#     customer_email = session.customer_details.email
#     subscription_id = session.subscription

#     # Try to find an existing user or create a new one
#     User = get_user_model()
#     try:
#         # Create a new user if they don't exist
#         user, created = User.objects.get_or_create(email=customer_email, defaults={
#             'username': customer_email.split("@")[0],  # Adjust to your needs
#             'password': User.objects.make_random_password(),  # Auto-generate password
#         })
#     except IntegrityError:
#         messages.error(request, "Error creating your account. Please contact support.")
#         return HttpResponseRedirect(reverse("subscription_details"))

#     # Sync the subscription from Stripe
#     try:
#         subscription = stripe.Subscription.retrieve(subscription_id)
#         djstripe_subscription = Subscription.sync_from_stripe_data(subscription)

#         # Set the subscription and customer on our user model
#         user.subscription = djstripe_subscription
#         user.customer, _ = Customer.get_or_create(subscriber=user)
#         user.save()

#         # Automatically log the user in (optional, depends on your flow)
#         login(request, user)

#         # Success message and redirect to a page
#         messages.success(request, "You've successfully signed up and an account was created for you!")
#         return HttpResponseRedirect(reverse("subscription_details"))

#     except stripe.error.StripeError as e:
#         # Handle errors from Stripe
#         messages.error(request, f"Stripe error: {e}")
#         return HttpResponseRedirect(reverse("subscription_details"))


# def subscription_confirm(request):
#     stripe_api_key = APIKey.objects.filter(livemode=False, type="secret").first()
#     if not stripe_api_key:
#         messages.error(request, "Stripe API key not found.")
#         return HttpResponseRedirect(reverse("home:home"))  # Update with correct view name

#     # Set the Stripe API key dynamically
#     stripe.api_key = str(stripe_api_key.secret)

#     # Get the session ID from the URL
#     session_id = str(request.GET.get("session_id"))
#     if not session_id:
#         messages.error(request, "Session ID is missing.")
#         return HttpResponseRedirect(reverse("home:home"))  # Update with correct view name

#     try:
#         # Retrieve session data from Stripe
#         session = stripe.checkout.Session.retrieve(session_id)

#         # Extract customer email from the session
#         customer_email = session.customer_details.email
#         subscription_id = session.subscription

#         # Try to find an existing user or create a new one
#         User = get_user_model()
#         user, created = User.objects.get_or_create(email=customer_email, defaults={
#             'username': customer_email,
#             'password': User.objects.make_random_password(),
#         })

#         # Sync the subscription from Stripe
#         subscription = stripe.Subscription.retrieve(subscription_id)
#         djstripe_subscription = Subscription.sync_from_stripe_data(subscription)

#         # Set the subscription and customer on the user model
#         user.subscription = djstripe_subscription
#         user.customer, _ = Customer.get_or_create(subscriber=user)
#         user.save()

#         auth_login(request, user)
        

#         # Success message and redirect to a page
#         if created:
#             messages.success(request, "You've successfully signed up, and an account was created for you!")
#         else:
#             messages.success(request, "Your subscription was successfully updated!")

#         return HttpResponseRedirect(reverse("text:add_text"))  # Update with correct view name

#     except stripe.error.StripeError as e:
#         # Handle errors from Stripe
#         messages.error(request, f"Stripe error: {e}")
#         return HttpResponseRedirect(reverse("home:home"))  # Update with correct view name

#     except IntegrityError:
#         messages.error(request, "Error creating your account. Please contact support.")
#         return HttpResponseRedirect(reverse("home:home"))  # Update with correct view name


from djstripe.models import Subscription, Customer
from django.contrib.auth import login as auth_login
from django.db import IntegrityError
import stripe
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse

def subscription_confirm(request):
    stripe_api_key = APIKey.objects.filter(livemode=False, type="secret").first()
    if not stripe_api_key:
        messages.error(request, "Stripe API key not found.")
        return HttpResponseRedirect(reverse("home:home"))  # Update with correct view name

    # Set the Stripe API key dynamically
    stripe.api_key = str(stripe_api_key.secret)

    # Get the session ID from the URL
    session_id = request.GET.get("session_id")
    if not session_id:
        messages.error(request, "Session ID is missing.")
        return HttpResponseRedirect(reverse("home:home"))  # Update with correct view name

    try:
        # Retrieve the session from Stripe
        session = stripe.checkout.Session.retrieve(session_id)

        # Extract customer email and subscription ID from the session
        customer_email = session.customer_details.email
        subscription_id = session.subscription

        # Retrieve or create the customer from Stripe data
        stripe_customer = stripe.Customer.retrieve(session.customer)
        djstripe_customer, created = Customer.get_or_create(
            defaults={'subscriber': None}
        )

        # Check if there's an existing user or create a new one based on the customer email
        User = get_user_model()
        user, user_created = User.objects.get_or_create(email=customer_email, defaults={
            'username': customer_email,
            'password': User.objects.make_random_password(),
        })

        # Link the user to the Stripe customer
        djstripe_customer.subscriber = user
        djstripe_customer.save()

        # Sync the subscription from Stripe
        subscription = stripe.Subscription.retrieve(subscription_id)
        djstripe_subscription = Subscription.sync_from_stripe_data(subscription)

        # Set the subscription on the user model (if needed)
        user.subscription = djstripe_subscription
        user.save()

        # Automatically log the user in
        auth_login(request, user)

        # Success message
        if user_created:
            messages.success(request, "You've successfully signed up, and an account was created for you!")
        else:
            messages.success(request, "Your subscription was successfully updated!")

        return HttpResponseRedirect(reverse("text:add_text"))  # Update with correct view name

    except stripe.error.StripeError as e:
        # Handle Stripe-related errors
        messages.error(request, f"Stripe error: {e}")
        return HttpResponseRedirect(reverse("home:home"))  # Update with correct view name

    except IntegrityError:
        # Handle database errors
        messages.error(request, "Error creating your account. Please contact support.")
        return HttpResponseRedirect(reverse("home:home"))  # Update with correct view name

    except Exception as e:
        # Catch any other unforeseen errors
        messages.error(request, f"An unexpected error occurred.{e}")
        return HttpResponseRedirect(reverse("home:home"))  # Update with correct view name
