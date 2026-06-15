from django.contrib import admin
from .models import SubscriptionPayment


@admin.register(SubscriptionPayment)
class SubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'business', 'plan', 'amount', 'currency', 'status', 'paid_at', 'created_at')
    list_filter = ('plan', 'status', 'currency')
    search_fields = ('user__email', 'business__name', 'stripe_payment_id', 'billing_email')
    date_hierarchy = 'created_at'
