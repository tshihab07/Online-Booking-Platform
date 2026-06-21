from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, PlatformSetting, SupportTicket


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'email',
        'username',
        'first_name',
        'last_name',
        'organization_name',
        'business_type',
        'role',
        'account_status',
        'is_staff',
        'is_active',
        'created_at',
    )
    list_filter = ('role', 'account_status', 'business_type', 'is_staff', 'is_active')
    search_fields = ('email', 'username', 'first_name', 'last_name', 'organization_name')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Profile', {
            'fields': (
                'first_name',
                'last_name',
                'phone',
                'organization_name',
                'business_type',
                'avatar',
                'role',
                'account_status',
                'admin_notes',
            )
        }),
        ('Multi-Tenancy', {'fields': ('businesses', 'active_business_id')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates', {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'account_status'),
        }),
    )


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('subject', 'user', 'priority', 'status', 'created_at')
    list_filter = ('priority', 'status')
    search_fields = ('subject', 'message', 'user__email')


@admin.register(PlatformSetting)
class PlatformSettingAdmin(admin.ModelAdmin):
    list_display = ('label', 'key', 'updated_at')
    search_fields = ('label', 'key')
