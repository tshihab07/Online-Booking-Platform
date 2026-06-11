from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('settings/', views.account_settings, name='settings'),
    path('settings/delete-account/', views.delete_account, name='delete_account'),
    path('support/', views.support_center, name='support'),
    path('switch-business/', views.switch_business, name='switch_business'),

    # Legacy URLs → KGB admin panel
    path('platform-admin/', RedirectView.as_view(url='/kgb-admin/', permanent=False)),
    path('platform-admin/<path:subpath>', RedirectView.as_view(url='/kgb-admin/', permanent=False)),
]
