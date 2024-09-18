from django.urls import path
from .views import PaymentAPI

urlpatterns = [
    path('make_payment/', PaymentAPI.as_view(), name='make_payment'),
    path("pricing-page/", views.pricing_page, name="pricing_page"),
    path("pricing-page-s/", views.embedded_pricing_page, name="embedded_pricing_page"),
    path("subscription-confirm/", views.subscription_confirm, name="subscription_confirm"),

]
