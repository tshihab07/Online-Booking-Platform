from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),

    # API documentation
    path('docs/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # Platform Admin Panel
    path('kgb-admin/', include('platform_admin.urls', namespace='platform_admin')),

    # Core / Marketing
    path('', include('core.urls')),

    # Auth
    path('', include('accounts.urls')),
    path('accounts/', include('allauth.urls')),

    # Dashboard
    path('dashboard/', include('businesses.urls')),

    # Public booking portal: /b/<slug>/
    path('b/<slug:slug>/', include('bookings.urls')),

    # Payments
    path('payments/', include('payments.urls')),

    # REST API v1
    path('api/v1/', include('api.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
