from django.db import models
from django.utils.text import slugify
import datetime

class Business(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    
    # Basic Info
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    business_type = models.CharField(max_length=50, choices=[
        ('restaurant', 'Restaurant'),
        ('hospital', 'Hospital'),
        ('salon', 'Salon'),
        ('event', 'Event Management'),
        ('hotel', 'Hotel'),
    ])
    
    # Contact
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    
    # Theme & Branding
    theme = models.CharField(max_length=50, default='default')
    logo = models.ImageField(upload_to='logos/', blank=True)
    hero_image = models.ImageField(upload_to='heroes/', blank=True)
    brand_colors = models.JSONField(default=dict)  # {"primary": "#ff0055", "secondary": "#00ff00"}
    custom_css = models.TextField(blank=True)
    
    # Working Hours
    working_hours = models.JSONField(default=dict)  # {"monday": {"open": "09:00", "close": "17:00"}}
    
    # Settings
    timezone = models.CharField(max_length=50, default='UTC')
    currency = models.CharField(max_length=3, default='USD')
    booking_lead_time = models.IntegerField(default=1)  # hours before booking
    max_booking_per_slot = models.IntegerField(default=1)
    buffer_time = models.IntegerField(default=0)  # minutes between bookings
    
    # Integrations
    stripe_account_id = models.CharField(max_length=100, blank=True)
    twilio_phone = models.CharField(max_length=20, blank=True)
    google_calendar_enabled = models.BooleanField(default=False)
    
    # Team
    team_members = models.JSONField(default=list)  # [{user_id, role, permissions}]
    
    # Subscription
    plan = models.CharField(max_length=20, default='free')
    subscription_status = models.CharField(max_length=20, default='active')
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    
    # Metadata
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'businesses'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name
    
    @property
    def booking_url(self):
        return f"https://{self.slug}.bookifypro.com"


class Service(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='services')
    
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    duration = models.IntegerField(help_text="Duration in minutes")
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to='services/', blank=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    max_capacity = models.IntegerField(default=1)  # For events/restaurants
    color = models.CharField(max_length=7, default='#3498db')  # Calendar color
    
    class Meta:
        db_table = 'services'
    
    def __str__(self):
        return self.name


class Staff(models.Model):
    _id = models.ObjectIdField(primary_key=True)
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='staff_members')
    
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(upload_to='staff/', blank=True)
    
    # Schedule
    availability = models.JSONField(default=dict)  # Custom hours per staff
    services = models.JSONField(default=list)  # List of service IDs this staff can perform
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'staff'