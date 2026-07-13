from django.urls import path
from . import views

app_name = 'businesses'

urlpatterns = [
    path('onboarding/', views.onboarding, name='onboarding'),
    path('', views.dashboard, name='dashboard'),

    # Calendar
    path('calendar/', views.calendar_view, name='calendar'),
    path('bookings/all-time/', views.all_time_bookings, name='all_time_bookings'),
    path('calendar/api/bookings/', views.calendar_bookings_api, name='calendar_bookings_api'),
    path('calendar/booking/<str:booking_id>/status/', views.update_booking_status, name='update_booking_status'),

    # Services
    path('services/', views.services_view, name='services'),
    path('services/add/', views.service_create, name='service_create'),
    path('services/<str:service_id>/edit/', views.service_edit, name='service_edit'),
    path('services/<str:service_id>/delete/', views.service_delete, name='service_delete'),

    # Staff
    path('staff/', views.staff_view, name='staff'),
    path('staff/add/', views.staff_create, name='staff_create'),
    path('staff/<str:staff_id>/edit/', views.staff_edit, name='staff_edit'),
    path('staff/<str:staff_id>/delete/', views.staff_delete, name='staff_delete'),

    # Settings / Site Builder
    path('settings/', views.settings_view, name='settings'),
    path('settings/theme/', views.update_theme, name='update_theme'),
    path('settings/colors/', views.update_brand_colors, name='update_brand_colors'),
    path('settings/hours/', views.update_working_hours, name='update_working_hours'),

    # CRM
    path('clients/', views.clients_view, name='clients'),
    path('clients/<str:client_id>/', views.client_detail, name='client_detail'),

    # Analytics
    path('analytics/', views.analytics_view, name='analytics'),

    # Marketing
    path('marketing/fill-gap/', views.fill_gap_view, name='fill_gap'),
]
