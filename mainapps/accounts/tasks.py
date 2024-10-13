from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import Credit

@shared_task
def reset_all_user_credits():
    monthly_credits = 100  # Define how many credits to add on reset
    now = timezone.now()

    # Fetch all Credit instances
    credits = Credit.objects.all()

    for credit in credits:
        if (now - credit.last_reset) >= timedelta(days=30):
            credit.reset_credits(monthly_credits)  # Reset credits
            print(f'Reset credits for user: {credit.user.id}')  # Log the action
