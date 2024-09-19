from django.urls import path
from .views import *
app_name='accounts'
urlpatterns=[
    path('login/',login,name='signin'),
    path('embedded_pricing_page/',embedded_pricing_page,name='embedded_pricing_page'),
    path('confirm-subscription/',subscription_confirm,name='subscription_confirm'),
]

# 4242 4242 4242 4242