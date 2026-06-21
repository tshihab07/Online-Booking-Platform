from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from .models import CustomUser, PlatformSetting, SupportTicket


class SignupForm(UserCreationForm):
    first_name = forms.CharField(
        label='First Name',
        widget=forms.TextInput(attrs={'placeholder': 'First name', 'class': 'form-input'}),
        required=True,
    )
    last_name = forms.CharField(
        label='Last Name',
        widget=forms.TextInput(attrs={'placeholder': 'Last name', 'class': 'form-input'}),
        required=True,
    )
    email = forms.EmailField(
        label='Email',
        widget=forms.EmailInput(attrs={'placeholder': 'your@email.com', 'class': 'form-input'}),
        required=True,
    )
    phone = forms.CharField(
        label='Phone Number',
        widget=forms.TextInput(attrs={'placeholder': '+1 234 567 8900', 'class': 'form-input'}),
        required=True,
    )
    organization_name = forms.CharField(
        label='Organization Name',
        widget=forms.TextInput(attrs={'placeholder': 'Your company or organization', 'class': 'form-input'}),
        required=True,
    )
    business_type = forms.ChoiceField(
        label='Business Type',
        choices=CustomUser.BUSINESS_TYPE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True,
    )
    username = forms.CharField(
        label='Username',
        widget=forms.TextInput(attrs={'placeholder': 'Choose a username', 'class': 'form-input'}),
        required=True,
    )
    agree_terms = forms.BooleanField(
        label='I agree to the Terms and Conditions',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
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
        fields = (
            'first_name',
            'last_name',
            'email',
            'phone',
            'organization_name',
            'business_type',
            'username',
            'password1',
            'password2',
            'agree_terms',
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['username']
        user.phone = self.cleaned_data['phone']
        user.organization_name = self.cleaned_data['organization_name']
        user.business_type = self.cleaned_data['business_type']
        user.account_status = 'pending'
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='Email or username',
        widget=forms.TextInput(attrs={'placeholder': 'Email or username', 'class': 'form-input', 'autofocus': True}),
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
