from django.urls import path
from . import views

app_name = 'api'

urlpatterns = [
    # Business
    path('businesses/<slug:slug>/', views.BusinessDetailAPI.as_view(), name='business_detail'),
    path('businesses/<slug:slug>/services/', views.BusinessServicesAPI.as_view(), name='business_services'),
    path('businesses/<slug:slug>/staff/', views.BusinessStaffAPI.as_view(), name='business_staff'),

    # Availability
    path('businesses/<slug:slug>/availability/', views.AvailabilityAPI.as_view(), name='availability'),
    path('businesses/<slug:slug>/heatmap/', views.HeatmapAPI.as_view(), name='heatmap'),

    # Bookings
    path('businesses/<slug:slug>/bookings/', views.BookingCreateAPI.as_view(), name='booking_create'),
    path('businesses/<slug:slug>/bookings/list/', views.BookingListAPI.as_view(), name='booking_list'),
    path('bookings/<str:pk>/', views.BookingDetailAPI.as_view(), name='booking_detail'),
]
