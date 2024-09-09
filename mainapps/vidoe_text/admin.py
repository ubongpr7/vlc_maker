from django.contrib import admin

# Register your models here.
from .models import TextFile,TextLineVideoClip

admin.site.register(TextLineVideoClip)
admin.site.register(TextFile)