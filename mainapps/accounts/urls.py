from django.urls import path
from .views import *
app_name='accounts'
urlpatterns=[
    path('login/',login,name='signin'),
    path('embedded_pricing_page/',embedded_pricing_page,name='embedded_pricing_page')
]