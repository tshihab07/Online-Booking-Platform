from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('checkout/<str:booking_id>/', views.create_checkout_session, name='checkout'),
    path('webhook/', views.stripe_webhook, name='webhook'),
]
