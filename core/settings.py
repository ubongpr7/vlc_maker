
import os
from pathlib import Path
# from celery.schedules import crontab

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-$*r+l*b2dxn-j-rk=r57ejwy575^g_x^+ac9a2jc&&w$&99mc&'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

DEFAULT_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]
THIRD_PARTY_APPS=[
    "bootstrap5",
    "django_htmx",
    'djstripe',
    'storages',
]
MAIN_APPS=[
    'mainapps.video',
    'mainapps.home',
    'mainapps.accounts',
    'mainapps.vidoe_text',
    'mainapps.audio',
]
INSTALLED_APPS=[

]
INSTALLED_APPS.extend(DEFAULT_APPS)
INSTALLED_APPS.extend(THIRD_PARTY_APPS)
INSTALLED_APPS.extend(MAIN_APPS)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR/'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
'''
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
'''
DATABASES = {
'default': {
'ENGINE': 'django.db.backends.postgresql',
'NAME': 'vlcdb1',
'USER': 'ubongpr7',
'PASSWORD':  os.getenv('DB_PASSWORD'),
'HOST': 'vlcdb1.cp8w6cg80sxf.eu-north-1.rds.amazonaws.com',
'PORT': '5432',
}
}

AUTH_USER_MODEL='accounts.User'

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        }
    },
]
# AUTH_PASSWORD_VALIDATORS = [
#     {
#         'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
#     },
#     {
#         'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
#     },
# ]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/


# EMAIL_BACKEND = 'django_smtp_ssl.SSLEmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST = 'smtp.office365.com'  # GoDaddy uses Office 365 for email
EMAIL_PORT = 587  
# EMAIL_PORT = 465  # SSL port
# EMAIL_USE_SSL = True
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')  
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER  # Default 'from' email address

DJSTRIPE_FOREIGN_KEY_TO_FIELD = "id"
STRIPE_LIVE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')

STRIPE_PRICING_TABLE_ID = "prctbl_1PzmCnEt5xiNvM25Ro8qIuJs"

DJSTRIPE_WEBHOOK_SECRET = "whsec_xxx"  # Get it from the section in the Stripe dashboard where you added the webhook endpoint
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

DOMAIN_NAME = "http://153.92.208.98:8000"

# Base configurations
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'  # This will be overridden for S3
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
# STATICFILES_STORAGE='django.contrib.staticfiles.storage.StaticFilesStorage'
# Media files (uploads by users)
MEDIA_URL = 'media/'  # This will be overridden for S3
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# DEFAULT_FILE_STORAGE='storages.backends.s3boto3.S3Boto3Storage'
# AWS S3 configuration
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = 'vlsmlsaker'
AWS_S3_REGION_NAME = 'eu-north-1'
AWS_S3_CUSTOM_DOMAIN = '%s.s3.amazonaws.com' % AWS_STORAGE_BUCKET_NAME
AWS_S3_FILES_OVERWRITE=False
STORAGES={
    "default":{
        'BACKEND':'storages.backends.s3boto3.S3Boto3Storage'
    },
    "staticfiles":{
        'BACKEND':'storages.backends.s3boto3.S3Boto3Storage'
    },
}
CELERY_BROKER_URL = 'redis://localhost:6379/0'  # URL for Redis
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'



CELERY_BEAT_SCHEDULE = {
    'reset-user-credits-every-30-days': {
        'task': 'yourapp.tasks.reset_all_user_credits',
        # 'schedule': crontab(hour=0, minute=0),  # Runs every day at midnight
    },
}

# Start the Celery worker
# celery -A core worker --loglevel=info

# # Start Celery Beat
# celery -A core beat --loglevel=info
PASSWORD_RESET_TIMEOUT = 3600

