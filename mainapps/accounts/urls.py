from django.urls import path
from .views import *
from django.contrib.auth import views as auth_views
app_name='accounts'
urlpatterns=[
    path('login/',login,name='signin'),
    path('embedded_pricing_page/',embedded_pricing_page,name='embedded_pricing_page'),
    # path('confirm-subscription/',subscription_confirm,name='subscription_confirm'),
    
    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset_done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),


]


# 4242 4242 4242 4242