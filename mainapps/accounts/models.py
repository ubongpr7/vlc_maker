# users/models.py

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    email = models.EmailField(unique=True, null=False, blank=False)
    api_key = models.CharField(max_length=255, blank=True, null=True)
    allowed_videos = models.IntegerField(default=0)  # Number of videos allowed based on subscription
    generated_videos = models.IntegerField(default=0)  # Track how many videos the user has generated
    subscription = models.ForeignKey(
        'djstripe.Subscription', null=True, blank=True, on_delete=models.SET_NULL,
        help_text="The user's Stripe Subscription object, if it exists"
    )
    customer = models.ForeignKey(
        'djstripe.Customer', null=True, blank=True, on_delete=models.SET_NULL,
        help_text="The user's Stripe Customer object, if it exists"
    )    
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def save(self, *args, **kwargs):
        self.username = self.email
        super().save(*args, **kwargs)

    def can_generate_video(self):
        return self.generated_videos < self.allowed_videos


class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100, unique=True)
    video_limit = models.IntegerField(default=5, help_text="Maximum number of videos a user can generate under this plan")

    def __str__(self):
        return self.name


class StripeSubscription(models.Model):
    start_date = models.DateTimeField(help_text="The start date of the subscription.")
    status = models.CharField(max_length=20, help_text="The status of this subscription.")
    # other data we need about the Subscription from Stripe goes here 


class MyStripeModel(models.Model):
    name = models.CharField(max_length=100)
    stripe_subscription = models.ForeignKey(StripeSubscription, on_delete=models.SET_NULL)