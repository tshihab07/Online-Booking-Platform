from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('', views.public_landing, name='landing'),
    path('step/<int:step>/', views.public_landing, name='landing_step'),
    path('api/availability/', views.api_availability, name='api_availability'),
    path('api/heatmap/', views.api_heatmap, name='api_heatmap'),
    path('api/staff-slots/', views.api_staff_slots, name='api_staff_slots'),
    path('book/', views.create_booking, name='create_booking'),
    path('confirmation/<str:booking_id>/', views.booking_confirmation, name='confirmation'),
    path('manage/<str:booking_id>/', views.manage_booking, name='manage_booking'),
]
