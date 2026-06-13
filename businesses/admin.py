from django.contrib import admin
from .models import Business, Service, Staff


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ('name', 'business_type', 'plan', 'is_active', 'created_at')
    list_filter = ('business_type', 'plan', 'is_active')
    search_fields = ('name', 'slug', 'email')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'duration', 'price', 'is_active')
    list_filter = ('is_active', 'business')
    search_fields = ('name', 'business__name')


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('name', 'business', 'email', 'is_active')
    list_filter = ('is_active', 'business')
    search_fields = ('name', 'email', 'business__name')
