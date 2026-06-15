from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from decouple import config
from decimal import Decimal
import random
from datetime import date, time, timedelta

from platform_admin.models import Plan

User = get_user_model()

PLANS = [
    dict(name='Free', tier='free', price=0, max_businesses=1, max_services=5,
         max_staff=3, max_bookings_per_month=50, max_calendar_views=100,
         custom_themes=False, analytics_enabled=True, api_access=False,
         priority_support=False, custom_domain=False, remove_branding=False),
    dict(name='Starter', tier='starter', price=19, max_businesses=1, max_services=20,
         max_staff=10, max_bookings_per_month=500, max_calendar_views=2000,
         custom_themes=True, analytics_enabled=True, api_access=False,
         priority_support=False, custom_domain=False, remove_branding=False),
    dict(name='Pro', tier='pro', price=49, max_businesses=3, max_services=100,
         max_staff=50, max_bookings_per_month=2000, max_calendar_views=10000,
         custom_themes=True, analytics_enabled=True, api_access=True,
         priority_support=True, custom_domain=True, remove_branding=False),
    dict(name='Enterprise', tier='enterprise', price=199, max_businesses=10,
         max_services=500, max_staff=200, max_bookings_per_month=10000,
         max_calendar_views=50000, custom_themes=True, analytics_enabled=True,
         api_access=True, priority_support=True, custom_domain=True, remove_branding=True),
]


class Command(BaseCommand):
    help = 'Initialise platform: create plans and optional demo data'

    def add_arguments(self, parser):
        parser.add_argument('--demo', action='store_true', help='Also create demo users/businesses/bookings')

    def handle(self, *args, **options):
        self._create_plans()
        if options['demo']:
            self._create_demo_data()
        self._print_credentials()

    # ------------------------------------------------------------------ plans
    def _create_plans(self):
        for data in PLANS:
            _, created = Plan.objects.get_or_create(tier=data['tier'], defaults=data)
            status = 'created' if created else 'already exists'
            self.stdout.write(f"  Plan [{data['tier']}]: {status}")

    # ------------------------------------------------------------ demo data
    def _create_demo_data(self):
        from businesses.models import Business, Service, Staff
        from bookings.models import Booking
        from payments.models import SubscriptionPayment
        from accounts.models import SupportTicket

        demo_password = 'demo12345'
        tier_map = {'free@demo.com': 'free', 'starter@demo.com': 'starter',
                    'pro@demo.com': 'pro', 'enterprise@demo.com': 'enterprise'}
        biz_templates = {
            'free': ('Glamour Salon', 'salon'),
            'starter': ('Taste Bistro', 'restaurant'),
            'pro': ('City Hospital', 'hospital'),
            'enterprise': ('Grand Hotel', 'hotel'),
        }
        svc_templates = {
            'salon': [('Haircut', 30, 25), ('Color', 90, 80)],
            'restaurant': [('Table for 2', 60, 0), ('Table for 4', 90, 0)],
            'hospital': [('Checkup', 30, 50), ('Specialist', 45, 100)],
            'hotel': [('Standard Room', 1440, 99), ('Suite', 1440, 199)],
        }

        for email, tier in tier_map.items():
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': tier.title(),
                    'last_name': 'Demo',
                    'account_status': 'approved',
                    'is_active': True,
                    'username': email.split('@')[0],
                }
            )
            if created:
                user.set_password(demo_password)
                user.save()
                self.stdout.write(f'  User created: {email}')

            biz_name, biz_type = biz_templates[tier]
            slug = f'demo-{biz_type}'
            # Use filter+create pattern to avoid passing empty _id to ObjectIdField
            biz = Business.objects.filter(slug=slug).first()
            biz_created = False
            if not biz:
                biz = Business.objects.create(
                    name=biz_name, slug=slug, business_type=biz_type,
                    email=email, phone='+1-555-0000',
                    plan=tier, is_active=True,
                )
                biz_created = True
            if biz_created:
                user.businesses = [str(biz.pk)]
                user.active_business_id = str(biz.pk)
                user.save()

            svcs = []
            for svc_name, dur, price in svc_templates.get(biz_type, []):
                svc = Service.objects.filter(business=biz, name=svc_name).first()
                if not svc:
                    svc = Service.objects.create(
                        business=biz, name=svc_name,
                        duration=dur, price=Decimal(str(price)), is_active=True
                    )
                svcs.append(svc)

            staff_obj = Staff.objects.filter(business=biz, email=f'staff@{slug}.com').first()
            if not staff_obj:
                staff_obj = Staff.objects.create(
                    business=biz, email=f'staff@{slug}.com',
                    name='Demo Staff', is_active=True
                )

            if svcs:
                for i in range(4):
                    b_date = date.today() + timedelta(days=i - 1)
                    b_time = time(10 + i, 0)
                    if not Booking.objects.filter(business=biz, customer_email=f'customer{i}@demo.com', date=b_date).exists():
                        Booking.objects.create(
                            business=biz,
                            customer_email=f'customer{i}@demo.com',
                            date=b_date,
                            start_time=b_time,
                            end_time=time(10 + i + 1, 0),
                            customer_name=f'Demo Customer {i+1}',
                            customer_phone='+1-555-1111',
                            service=svcs[0],
                            staff=staff_obj,
                            status=random.choice(['confirmed', 'completed', 'pending']),
                            amount=Decimal(str(svcs[0].price)),
                            payment_status=random.choice(['paid', 'unpaid']),
                        )

            sp = SubscriptionPayment.objects.filter(user=user, business=biz, plan=tier).first()
            if not sp:
                SubscriptionPayment.objects.create(
                    user=user, business=biz, plan=tier,
                    amount=Decimal(str({'free': 0, 'starter': 19, 'pro': 49, 'enterprise': 199}[tier])),
                    status='paid',
                    billing_email=email,
                )

            if not SupportTicket.objects.filter(user=user, subject='Demo Ticket').exists():
                SupportTicket.objects.create(
                    user=user, subject='Demo Ticket',
                    message='This is a demo support ticket.',
                    status='open', priority='normal',
                )

        self.stdout.write(self.style.SUCCESS('Demo data ready.'))

    # --------------------------------------------------------- print summary
    def _print_credentials(self):
        admin_user = config('ADMIN_USERNAME', default='bookify2029')
        admin_pass = config('ADMIN_PASSWORD', default='(see .env)')
        su_email = config('SUPERUSER_EMAIL', default='(see .env)')
        su_pass = config('SUPERUSER_PASSWORD', default='(see .env)')

        self.stdout.write(self.style.SUCCESS('\n' + '=' * 55))
        self.stdout.write(self.style.SUCCESS('  PLATFORM READY'))
        self.stdout.write(self.style.SUCCESS('=' * 55))
        self.stdout.write(f'\n  KGB Admin Panel   → http://127.0.0.1:8000/kgb-admin/')
        self.stdout.write(f'    Username : {admin_user}')
        self.stdout.write(f'    Password : {admin_pass}')
        self.stdout.write(f'\n  Django Admin      → http://127.0.0.1:8000/admin/')
        self.stdout.write(f'    Email    : {su_email}')
        self.stdout.write(f'    Password : {su_pass}')
        self.stdout.write(f'\n  Demo Users (password: demo12345)')
        self.stdout.write(f'    free@demo.com  / starter@demo.com')
        self.stdout.write(f'    pro@demo.com   / enterprise@demo.com')
        self.stdout.write(f'\n  User Login        → http://127.0.0.1:8000/login/')
        self.stdout.write(f'  User Dashboard    → http://127.0.0.1:8000/dashboard/')
        self.stdout.write(self.style.SUCCESS('=' * 55 + '\n'))
