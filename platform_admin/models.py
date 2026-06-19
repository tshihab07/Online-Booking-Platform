from django.db import models
from django.conf import settings


class Plan(models.Model):
    """Subscription plans with feature limits"""
    TIER_CHOICES = [
        ('free', 'Free'),
        ('starter', 'Starter'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ]
    
    name = models.CharField(max_length=50, unique=True)
    tier = models.CharField(max_length=20, choices=TIER_CHOICES, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    
    # Feature limits
    max_businesses = models.IntegerField(default=1)
    max_services = models.IntegerField(default=10)
    max_staff = models.IntegerField(default=5)
    max_bookings_per_month = models.IntegerField(default=100)
    max_calendar_views = models.IntegerField(default=500)
    
    # Features
    custom_themes = models.BooleanField(default=False)
    analytics_enabled = models.BooleanField(default=True)
    api_access = models.BooleanField(default=False)
    priority_support = models.BooleanField(default=False)
    custom_domain = models.BooleanField(default=False)
    remove_branding = models.BooleanField(default=False)
    
    # Stripe
    stripe_price_id = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'platform_plans'
        ordering = ['price']
    
    def __str__(self):
        return self.name


class Announcement(models.Model):
    """Platform-wide announcements"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('maintenance', 'Maintenance'),
        ('feature', 'New Feature'),
        ('update', 'Update'),
    ]
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    announcement_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Targeting
    target_all = models.BooleanField(default=True)
    target_plans = models.JSONField(default=list, blank=True)  # List of plan tiers
    
    # Scheduling
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    # Dismissible
    is_dismissible = models.BooleanField(default=True)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'platform_announcements'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title


class UserUsage(models.Model):
    """Track user usage for limits"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='usage')
    
    # Current month usage
    bookings_this_month = models.IntegerField(default=0)
    api_calls_this_month = models.IntegerField(default=0)
    storage_used_mb = models.FloatField(default=0)
    
    # All time
    total_bookings = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    
    # Reset tracking
    last_reset = models.DateField(auto_now_add=True)
    
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'platform_user_usage'
    
    def __str__(self):
        return f"Usage for {self.user.email}"
    
    def reset_monthly(self):
        """Reset monthly counters"""
        from django.utils import timezone
        self.bookings_this_month = 0
        self.api_calls_this_month = 0
        self.last_reset = timezone.now().date()
        self.save()


class AuditLog(models.Model):
    """Audit trail for admin actions"""
    ACTION_CHOICES = [
        ('user_create', 'User Created'),
        ('user_update', 'User Updated'),
        ('user_suspend', 'User Suspended'),
        ('user_delete', 'User Deleted'),
        ('user_activate', 'User Activated'),
        ('business_deactivate', 'Business Deactivated'),
        ('business_activate', 'Business Activated'),
        ('plan_change', 'Plan Changed'),
        ('payment_refund', 'Payment Refunded'),
        ('ticket_resolve', 'Ticket Resolved'),
        ('announcement_create', 'Announcement Created'),
        ('settings_update', 'Settings Updated'),
    ]
    
    admin_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    target_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_entries')
    target_business_id = models.CharField(max_length=50, blank=True)
    details = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'platform_audit_logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_action_display()} by {self.admin_user}"
