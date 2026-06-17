from django.contrib import admin
from .models import Plan, Announcement, UserUsage, AuditLog


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'tier', 'price', 'is_active', 'max_bookings_per_month']
    list_filter = ['tier', 'is_active']
    search_fields = ['name']


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'announcement_type', 'status', 'published_at']
    list_filter = ['status', 'announcement_type']
    search_fields = ['title', 'message']


@admin.register(UserUsage)
class UserUsageAdmin(admin.ModelAdmin):
    list_display = ['user', 'bookings_this_month', 'total_bookings', 'last_reset']
    search_fields = ['user__email']


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'admin_user', 'target_user', 'created_at']
    list_filter = ['action']
    search_fields = ['admin_user__email', 'target_user__email']
    readonly_fields = ['admin_user', 'action', 'target_user', 'target_business_id', 'details', 'ip_address', 'created_at']
