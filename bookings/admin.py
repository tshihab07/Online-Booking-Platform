from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'business', 'service', 'date', 'start_time', 'status', 'amount', 'payment_status')
    list_filter = ('status', 'payment_status', 'date', 'business')
    search_fields = ('customer_name', 'customer_email', 'customer_phone')
    readonly_fields = ('created_at',)
    date_hierarchy = 'date'
    ordering = ('-date', '-start_time')
