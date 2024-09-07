
from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('mainapps.accounts.urls',namespace='accounts')),
    path('', include('mainapps.home.urls',namespace='home')),
    path('video/', include('mainapps.video.urls',namespace='video')),
    path('text/', include('mainapps.vidoe_text.urls',namespace='video_text')),
]
