from django.apps import AppConfig


class PlatformAdminConfig(AppConfig):
    default_auto_field = 'django_mongodb_backend.fields.ObjectIdAutoField'
    name = 'platform_admin'
    verbose_name = 'Platform Administration'
