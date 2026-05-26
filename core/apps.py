from django.apps import AppConfig


class CoreConfig(AppConfig):
    name = 'core'

    def ready(self):
        from django.db.models.signals import post_migrate
        post_migrate.disconnect(
            dispatch_uid='django.contrib.auth.management.create_permissions'
        )
