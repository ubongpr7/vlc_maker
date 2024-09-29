
from django.contrib import admin
from django.urls import path,include
from django.conf import settings
from django.conf.urls.static import static

from mainapps.accounts.emails import CustomPasswordResetView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('mainapps.accounts.urls',namespace='accounts')),
    path('', include('mainapps.home.urls',namespace='home')),
    path('video/', include('mainapps.video.urls',namespace='video')),
    path('text/', include('mainapps.vidoe_text.urls',namespace='video_text')),
    path("stripe/", include("djstripe.urls", namespace="djstripe")),
    path("auth/", include("django.contrib.auth.urls")),  # new
    path('auth/password_reset/', CustomPasswordResetView.as_view(), name='password_reset'),

]+static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# accounts/login/ [name='login']
# accounts/logout/ [name='logout']
# accounts/password_change/ [name='password_change']
# accounts/password_change/done/ [name='password_change_done']
# accounts/password_reset/ [name='password_reset']
# accounts/password_reset/done/ [name='password_reset_done']
# accounts/reset/<uidb64>/<token>/ [name='password_reset_confirm']
# accounts/reset/done/ [name='password_reset_complete']