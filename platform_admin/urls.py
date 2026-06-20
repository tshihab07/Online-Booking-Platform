from django.urls import path
from . import views

app_name = 'platform_admin'

urlpatterns = [
    # Auth
    path('login/', views.platform_admin_login_view, name='login'),
    path('logout/', views.platform_admin_logout_view, name='logout'),
    
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Users
    path('users/', views.user_list, name='users'),
    path('users/<str:user_id>/', views.user_detail, name='user_detail'),
    path('users/<str:user_id>/change-plan/', views.user_change_plan, name='user_change_plan'),
    path('users/<str:user_id>/impersonate/', views.impersonate_user, name='impersonate_user'),
    
    # Businesses
    path('businesses/', views.business_list, name='businesses'),
    path('businesses/<str:business_id>/', views.business_detail, name='business_detail'),
    
    # Bookings
    path('bookings/', views.booking_list, name='bookings'),
    
    # Payments
    path('payments/', views.payment_list, name='payments'),
    path('payments/<str:payment_id>/', views.payment_detail, name='payment_detail'),
    
    # Support
    path('support/', views.support_list, name='support'),
    path('support/<str:ticket_id>/', views.support_detail, name='support_detail'),
    
    # Plans
    path('plans/', views.plan_list, name='plans'),
    path('plans/<str:plan_id>/edit/', views.plan_edit, name='plan_edit'),
    
    # Announcements
    path('announcements/', views.announcement_list, name='announcements'),
    path('announcements/<str:announcement_id>/edit/', views.announcement_edit, name='announcement_edit'),
    
    # Settings
    path('settings/', views.settings_view, name='settings'),
    
    # Audit
    path('audit/', views.audit_logs, name='audit_logs'),
    
    # Impersonation
    path('stop-impersonation/', views.stop_impersonation, name='stop_impersonation'),
]
