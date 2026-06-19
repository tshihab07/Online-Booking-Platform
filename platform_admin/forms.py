from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.utils.translation import gettext_lazy as _
from .models import Announcement, Plan


class PlatformAdminLoginForm(AuthenticationForm):
    """Custom login form for platform admin"""
    username = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={
            'placeholder': 'admin@example.com',
            'class': 'form-input',
            'autofocus': True,
            'autocomplete': 'email'
        })
    )
    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'placeholder': '••••••••',
            'class': 'form-input',
            'autocomplete': 'current-password'
        })
    )


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = '__all__'
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'tier': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'max_businesses': forms.NumberInput(attrs={'class': 'form-input'}),
            'max_services': forms.NumberInput(attrs={'class': 'form-input'}),
            'max_staff': forms.NumberInput(attrs={'class': 'form-input'}),
            'max_bookings_per_month': forms.NumberInput(attrs={'class': 'form-input'}),
            'max_calendar_views': forms.NumberInput(attrs={'class': 'form-input'}),
            'stripe_price_id': forms.TextInput(attrs={'class': 'form-input'}),
        }


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = '__all__'
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-input'}),
            'message': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 5}),
            'announcement_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'target_plans': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 4}),
            'published_at': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
            'expires_at': forms.DateTimeInput(attrs={'class': 'form-input', 'type': 'datetime-local'}),
        }


class UserSearchForm(forms.Form):
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-input',
        'placeholder': 'Search by email, name...'
    }))
    status = forms.ChoiceField(required=False, choices=[('', 'All Status')] + [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('suspended', 'Suspended'),
        ('rejected', 'Rejected'),
    ], widget=forms.Select(attrs={'class': 'form-select'}))
    plan = forms.ChoiceField(required=False, widget=forms.Select(attrs={'class': 'form-select'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        plan_choices = [('', 'All Plans')]
        from .models import Plan
        for plan in Plan.objects.filter(is_active=True):
            plan_choices.append((plan.tier, plan.name))
        self.fields['plan'].choices = plan_choices


class BusinessSearchForm(forms.Form):
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-input',
        'placeholder': 'Search by name, slug...'
    }))
    business_type = forms.ChoiceField(required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    status = forms.ChoiceField(required=False, choices=[('', 'All'), ('active', 'Active'), ('inactive', 'Inactive')],
                               widget=forms.Select(attrs={'class': 'form-select'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from businesses.models import Business
        type_choices = [('', 'All Types')]
        for code, name in Business._meta.get_field('business_type').choices:
            type_choices.append((code, name))
        self.fields['business_type'].choices = type_choices


class BookingFilterForm(forms.Form):
    search = forms.CharField(required=False, widget=forms.TextInput(attrs={
        'class': 'form-input',
        'placeholder': 'Search customer...'
    }))
    status = forms.ChoiceField(required=False, widget=forms.Select(attrs={'class': 'form-select'}))
    date_from = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}))
    date_to = forms.DateField(required=False, widget=forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from bookings.models import Booking
        status_choices = [('', 'All Status')]
        for code, name in Booking.STATUS_CHOICES:
            status_choices.append((code, name))
        self.fields['status'].choices = status_choices


class AnnouncementDismissForm(forms.Form):
    announcement_id = forms.CharField(widget=forms.HiddenInput())
