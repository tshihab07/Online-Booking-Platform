from django import forms
from .models import Business, Service, Staff

DAYS = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']


class OnboardingForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = ('name', 'business_type', 'email', 'phone', 'address', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Your Business Name'}),
            'business_type': forms.Select(attrs={'class': 'form-select'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }


class BusinessSettingsForm(forms.ModelForm):
    class Meta:
        model = Business
        fields = (
            'name', 'description', 'email', 'phone', 'address', 'website',
            'timezone', 'currency', 'booking_lead_time', 'max_booking_per_slot',
            'buffer_time', 'logo', 'hero_image', 'custom_css',
        )
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'address': forms.TextInput(attrs={'class': 'form-input'}),
            'website': forms.URLInput(attrs={'class': 'form-input'}),
            'timezone': forms.TextInput(attrs={'class': 'form-input'}),
            'currency': forms.TextInput(attrs={'class': 'form-input', 'maxlength': 3}),
            'booking_lead_time': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'max_booking_per_slot': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'buffer_time': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'custom_css': forms.Textarea(attrs={'class': 'form-textarea font-mono', 'rows': 6}),
        }


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ('name', 'description', 'duration', 'price', 'category', 'image', 'max_capacity', 'color', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
            'duration': forms.NumberInput(attrs={'class': 'form-input', 'min': 5}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'step': '0.01'}),
            'category': forms.TextInput(attrs={'class': 'form-input'}),
            'max_capacity': forms.NumberInput(attrs={'class': 'form-input', 'min': 1}),
            'color': forms.TextInput(attrs={'class': 'form-input', 'type': 'color'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }


class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ('name', 'email', 'phone', 'bio', 'avatar', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'bio': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
        }
