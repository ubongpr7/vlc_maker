from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
import threading
from django.contrib.auth.views import PasswordResetView
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.http import HttpResponseRedirect


from django.contrib.auth import login
from django.contrib.auth.views import PasswordResetConfirmView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils.http import urlsafe_base64_decode

from mainapps.accounts.models import User


class EmailThread(threading.Thread):
    def __init__(self, email_message):
        self.email_message = email_message
        threading.Thread.__init__(self)

    def run(self):
        print("Initializing thread")
        self.email_message.send()
        if self.email_message.send():
            print('Email sent successfully')


def send_html_email(subject, message, from_email, to_email, html_file, context):
    html_content = render_to_string(html_file, context)
    text_content = strip_tags(html_content)

    msg = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
    msg.attach_alternative(html_content, "text/html")
    print("Sending email...")
    EmailThread(msg).start()


def send_user_password_email(user):
    # Generate a password reset link using Django's token generator
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    
    # Build the password reset link using Django's built-in views
    password_reset_link = f"{settings.DOMAIN_NAME}{reverse('password_reset_confirm', kwargs={'uidb64': uid, 'token': token})}"
    
    # Prepare the email context
    context = {
        'user_name': user.username,
    }

    # Send the email with the custom template
    send_html_email(
        subject="Welcome to CreativeMaker.io – Let’s Create Some Amazing Creatives!",
        message=None,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to_email=user.email,
        html_file='accounts/password_reset.html',  # Path to your HTML email template
        context=context
    )

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    # Override the default success URL (redirect to '/text')
    success_url = '/text'

    def form_valid(self, form):
        # Reset the password
        response = super().form_valid(form)

        # Automatically log the user in after password reset
        user = form.user
        login(self.request, user)

        # Redirect to the desired page after login
        return redirect(self.success_url)
    

class CustomPasswordResetView(PasswordResetView):
    html_email_template_name = 'registration/password_reset_email.html'  # HTML email template

    def send_mail(self, subject_template_name, email_template_name, context, from_email, to_email, html_email_template_name=None, use_django_email=True):
        # Render the subject and email context
        subject = render_to_string(subject_template_name, context).strip()
        html_file = html_email_template_name or self.html_email_template_name
        
        # Call your custom function to send the HTML email
        send_html_email(
            subject=subject,
            message=None,  # Since you're using HTML, no need for a plain message here
            from_email=from_email,
            to_email=to_email,
            html_file=html_file,
            context=context
        )