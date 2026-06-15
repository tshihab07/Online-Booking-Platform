from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from businesses.models import Business, Service, Staff
from bookings.models import Booking
from payments.models import SubscriptionPayment
from accounts.models import SupportTicket
from platform_admin.models import Plan
from datetime import date, time, timedelta
from decimal import Decimal
import random

User = get_user_model()


class Command(BaseCommand):
    help = 'Create demo data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating demo data...')
        
        # Ensure plans exist
        if not Plan.objects.exists():
            from .create_superuser import Command as CreateSuperuser
            CreateSuperuser()._create_default_plans()
        
        # Create demo users
        users = self._create_users()
        
        # Create businesses
        businesses = self._create_businesses(users)
        
        # Create services
        services = self._create_services(businesses)
        
        # Create staff
        staff = self._create_staff(businesses)
        
        # Create bookings
        self._create_bookings(businesses, services, staff)
        
        # Create payments
        self._create_payments(users, businesses)
        
        # Create support tickets
        self._create_tickets(users)
        
        self.stdout.write(self.style.SUCCESS('Demo data created successfully!'))

    def _create_users(self):
        users = []
        test_users = [
            ('free@demo.com', 'Demo Free', 'free'),
            ('starter@demo.com', 'Demo Starter', 'starter'),
            ('pro@demo.com', 'Demo Pro', 'pro'),
            ('enterprise@demo.com', 'Demo Enterprise', 'enterprise'),
        ]
        
        for email, name, plan in test_users:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': name.split()[0],
                    'last_name': name.split()[1] if len(name.split()) > 1 else '',
                    'account_status': 'approved',
                    'is_active': True,
                }
            )
            if created:
                user.set_password('demo12345')
                user.save()
                self.stdout.write(f'Created user: {email}')
            users.append((user, plan))
        return users

    def _create_businesses(self, users):
        businesses = []
        business_data = [
            ('Glamour Salon', 'salon'),
            ('Taste Bistro', 'restaurant'),
            ('City Hospital', 'hospital'),
            ('Grand Hotel', 'hotel'),
            ('Event Masters', 'event'),
        ]
        
        for i, (user, plan) in enumerate(users):
            name, btype = business_data[i % len(business_data)]
            business, created = Business.objects.get_or_create(
                slug=f'demo-{btype}-{i}',
                defaults={
                    'name': name,
                    'business_type': btype,
                    'email': user.email,
                    'phone': f'+1-555-{100+i:03d}',
                    'address': f'{100+i} Demo Street, Demo City',
                    'plan': plan,
                    'is_active': True,
                }
            )
            if created:
                user.businesses = [str(business.pk)]
                user.active_business_id = str(business.pk)
                user.save()
                self.stdout.write(f'Created business: {name}')
            businesses.append(business)
        return businesses

    def _create_services(self, businesses):
        services = []
        service_templates = {
            'salon': [('Haircut', 30, 25), ('Color', 90, 80), ('Styling', 45, 40)],
            'restaurant': [('Table for 2', 60, 0), ('Table for 4', 90, 0), ('Private Dining', 120, 100)],
            'hospital': [('General Checkup', 30, 50), ('Specialist Consult', 45, 100), ('Lab Work', 15, 75)],
            'hotel': [('Standard Room', 1440, 99), ('Deluxe Suite', 1440, 199), ('Conference Room', 240, 150)],
            'event': [('Wedding Package', 480, 500), ('Corporate Event', 240, 300), ('Birthday Party', 180, 150)],
        }
        
        for business in businesses:
            templates = service_templates.get(business.business_type, service_templates['salon'])
            for name, duration, price in templates:
                service, created = Service.objects.get_or_create(
                    business=business,
                    name=name,
                    defaults={'duration': duration, 'price': Decimal(str(price)), 'is_active': True}
                )
                if created:
                    services.append(service)
        return services

    def _create_staff(self, businesses):
        staff_list = []
        for business in businesses:
            for i in range(2):
                member, created = Staff.objects.get_or_create(
                    business=business,
                    email=f'staff{i}@{business.slug}.com',
                    defaults={'name': f'Staff Member {i+1}', 'is_active': True}
                )
                if created:
                    staff_list.append(member)
        return staff_list

    def _create_bookings(self, businesses, services, staff):
        customer_names = ['John Doe', 'Jane Smith', 'Bob Wilson', 'Alice Brown', 'Charlie Davis']
        
        for business in businesses:
            business_services = [s for s in services if s.business_id == business.pk]
            business_staff = [s for s in staff if s.business_id == business.pk]
            
            for i in range(5):
                booking_date = date.today() + timedelta(days=i-2)
                booking, created = Booking.objects.get_or_create(
                    business=business,
                    customer_email=f'customer{i}@demo.com',
                    date=booking_date,
                    start_time=time(10 + i, 0),
                    defaults={
                        'customer_name': random.choice(customer_names),
                        'customer_phone': '+1-555-0000',
                        'service': random.choice(business_services) if business_services else None,
                        'staff': random.choice(business_staff) if business_staff else None,
                        'status': random.choice(['confirmed', 'completed', 'pending']),
                        'amount': Decimal(str(random.randint(25, 150))),
                        'payment_status': random.choice(['paid', 'unpaid']),
                    }
                )

    def _create_payments(self, users, businesses):
        for user, plan in users:
            payment, created = SubscriptionPayment.objects.get_or_create(
                user=user,
                business=businesses[users.index((user, plan))],
                plan=plan,
                defaults={
                    'amount': Decimal(str({'free': 0, 'starter': 19, 'pro': 49, 'enterprise': 199}.get(plan, 0))),
                    'status': 'paid',
                    'billing_email': user.email,
                }
            )

    def _create_tickets(self, users):
        for user, _ in users[:2]:
            ticket, created = SupportTicket.objects.get_or_create(
                user=user,
                subject='Demo Support Ticket',
                defaults={
                    'message': 'This is a demo support ticket for testing.',
                    'status': 'open',
                    'priority': 'normal',
                }
            )
