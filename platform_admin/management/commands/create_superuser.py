from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decouple import config

User = get_user_model()


class Command(BaseCommand):
    help = 'Create Django /admin/ superuser from SUPERUSER_* vars in .env'

    def handle(self, *args, **options):
        email = config('SUPERUSER_EMAIL', default=None)
        password = config('SUPERUSER_PASSWORD', default=None)
        username = config('SUPERUSER_USERNAME', default=None)

        if not email or not password:
            self.stdout.write(self.style.ERROR(
                'SUPERUSER_EMAIL and SUPERUSER_PASSWORD must be set in .env'
            ))
            return

        if User.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f'Superuser already exists: {email}'))
        else:
            User.objects.create_superuser(
                email=email,
                password=password,
                username=username or email.split('@')[0],
            )
            self.stdout.write(self.style.SUCCESS(f'Django superuser created: {email}'))

        self.stdout.write(self.style.SUCCESS(
            '\nDjango /admin/ credentials:\n'
            f'  Email   : {email}\n'
            f'  Password: {password}\n'
            f'  URL     : http://127.0.0.1:8000/admin/\n'
        ))
        self.stdout.write(self.style.WARNING(
            'KGB Admin panel (/kgb-admin/) uses ADMIN_USERNAME + ADMIN_PASSWORD from .env\n'
            'Run: python manage.py init_platform  to create plans and demo data.\n'
        ))
