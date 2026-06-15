from django import forms
from .models import SubscriptionPayment


class SubscriptionPaymentForm(forms.ModelForm):
    class Meta:
        model = SubscriptionPayment
        fields = ('plan', 'amount', 'currency', 'status', 'stripe_payment_id', 'billing_email', 'paid_at')
        widgets = {
            'plan': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'currency': forms.TextInput(attrs={'class': 'form-input', 'maxlength': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'stripe_payment_id': forms.TextInput(attrs={'class': 'form-input'}),
            'billing_email': forms.EmailInput(attrs={'class': 'form-input'}),
            'paid_at': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
        }
