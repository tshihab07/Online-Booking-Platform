from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from .models import CustomUser, PlatformSetting, SupportTicket


class SignupForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'your@email.com', 'class': 'form-input'})
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': 'form-input'}),
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': 'form-input'}),
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email
        user.account_status = 'pending'
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'your@email.com', 'class': 'form-input', 'autofocus': True}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': '••••••••', 'class': 'form-input'}),
    )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone', 'avatar')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input', 'placeholder': '+1 234 567 8900'}),
        }


class AccountSettingsForm(ProfileForm):
    pass


class SupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ('subject', 'priority', 'message')
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-input'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'message': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 5}),
        }


class StyledPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-input'}))


class AdminUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'phone', 'role', 'account_status', 'is_active', 'is_staff', 'admin_notes')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-input'}),
            'last_name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'phone': forms.TextInput(attrs={'class': 'form-input'}),
            'role': forms.TextInput(attrs={'class': 'form-input'}),
            'account_status': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'is_staff': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'admin_notes': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 4}),
        }


class AdminPasswordResetForm(forms.Form):
    new_password = forms.CharField(
        min_length=8,
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'autocomplete': 'new-password'}),
    )


class AdminSupportTicketForm(forms.ModelForm):
    class Meta:
        model = SupportTicket
        fields = ('status', 'priority', 'admin_response')
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'priority': forms.Select(attrs={'class': 'form-select'}),
            'admin_response': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 6}),
        }


class PlatformSettingForm(forms.ModelForm):
    class Meta:
        model = PlatformSetting
        fields = ('label', 'key', 'value', 'description')
        widgets = {
            'label': forms.TextInput(attrs={'class': 'form-input'}),
            'key': forms.TextInput(attrs={'class': 'form-input'}),
            'value': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 5}),
            'description': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 3}),
        }
