from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Count, Sum
from django.utils import timezone
from .forms import (
    AccountSettingsForm,
    AdminPasswordResetForm,
    AdminSupportTicketForm,
    AdminUserForm,
    LoginForm,
    PlatformSettingForm,
    ProfileForm,
    SignupForm,
    StyledPasswordChangeForm,
    SupportTicketForm,
)
from .models import CustomUser, PlatformSetting, SupportTicket


def _user_has_business(user):
    from businesses.models import Business

    active_id = user.active_business_id
    if active_id and Business.objects.filter(pk=active_id).exists():
        return True
    ids = user.businesses or []
    return bool(ids) and Business.objects.filter(pk__in=ids).exists()


def staff_required(view_func):
    return login_required(user_passes_test(lambda u: u.is_staff and u.is_active)(view_func))


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('businesses:dashboard')
    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, 'Welcome to Bookify! Let\'s set up your business.')
        return redirect('businesses:onboarding')
    return render(request, 'accounts/signup.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        if request.user.is_authenticated:
            logout(request)

        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('businesses:dashboard')
        return render(request, 'accounts/login.html', {'form': form})

    if request.GET.get('switch') == '1' and request.user.is_authenticated:
        logout(request)
        messages.info(request, 'Signed out. Log in with your existing account below.')
        return redirect('accounts:login')

    if request.user.is_authenticated:
        if _user_has_business(request.user):
            return redirect('businesses:dashboard')
        return render(request, 'accounts/login.html', {
            'form': LoginForm(request),
            'pending_setup': True,
            'current_email': request.user.email,
        })

    initial = {}
    email = request.GET.get('email', '').strip()
    if email:
        initial['username'] = email

    form = LoginForm(request, initial=initial)
    return render(request, 'accounts/login.html', {'form': form})


def _auth_path_not_found(request, extra_path, auth_action):
    """Handle invalid /login/<extra> or /signup/<extra> URLs with a friendly page."""
    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError

    suggested_email = ''
    if auth_action == 'login' and extra_path:
        candidate = extra_path.strip('/')
        try:
            validate_email(candidate)
            suggested_email = candidate
        except ValidationError:
            pass

    return render(request, 'accounts/auth_path_not_found.html', {
        'auth_action': auth_action,
        'page_label': 'Log In' if auth_action == 'login' else 'Sign Up',
        'request_path': request.path,
        'suggested_email': suggested_email,
    }, status=404)


def login_path_not_found_view(request, extra_path):
    return _auth_path_not_found(request, extra_path, 'login')


def signup_path_not_found_view(request, extra_path):
    return _auth_path_not_found(request, extra_path, 'signup')


@require_POST
def logout_view(request):
    logout(request)
    return redirect('core:home')


@login_required
def profile_view(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def account_settings(request):
    profile_form = AccountSettingsForm(request.POST or None, request.FILES or None, instance=request.user)
    password_form = StyledPasswordChangeForm(request.user, request.POST or None, prefix='password')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'profile' and profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Account details updated.')
            return redirect('accounts:settings')
        if action == 'password' and password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Password updated.')
            return redirect('accounts:settings')

    return render(request, 'accounts/settings.html', {
        'profile_form': profile_form,
        'password_form': password_form,
        'page': 'account_settings',
    })


@login_required
@require_POST
def delete_account(request):
    if request.POST.get('confirm_email') != request.user.email:
        messages.error(request, 'Type your exact email address to delete the account.')
        return redirect('accounts:settings')
    request.user.is_active = False
    request.user.account_status = 'suspended'
    request.user.save(update_fields=['is_active', 'account_status'])
    logout(request)
    messages.success(request, 'Your account has been deactivated.')
    return redirect('core:home')


@login_required
def support_center(request):
    form = SupportTicketForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        ticket = form.save(commit=False)
        ticket.user = request.user
        ticket.save()
        messages.success(request, 'Support ticket submitted.')
        return redirect('accounts:support')

    tickets = SupportTicket.objects.filter(user=request.user)
    return render(request, 'accounts/support.html', {
        'form': form,
        'tickets': tickets,
        'page': 'support',
    })


@login_required
@require_POST
def switch_business(request):
    from businesses.models import Business
    business_id = request.POST.get('business_id')
    business = get_object_or_404(Business, pk=business_id)
    user = request.user
    if str(business_id) in [str(b) for b in (user.businesses or [])]:
        user.active_business_id = str(business_id)
        user.save(update_fields=['active_business_id'])
    return redirect('businesses:dashboard')


@staff_required
def platform_admin_dashboard(request):
    from bookings.models import Booking
    from businesses.models import Business
    from payments.models import SubscriptionPayment

    today = timezone.localdate()
    users = CustomUser.objects.all().order_by('-created_at')
    bookings = Booking.objects.all()
    payments = SubscriptionPayment.objects.all()
    paid_payments = payments.filter(status='paid')

    metrics = {
        'total_users': users.count(),
        'pending_users': users.filter(account_status='pending').count(),
        'active_businesses': Business.objects.filter(is_active=True).count(),
        'total_bookings': bookings.count(),
        'open_tickets': SupportTicket.objects.exclude(status__in=['resolved', 'closed']).count(),
        'subscription_income': paid_payments.aggregate(total=Sum('amount')).get('total') or 0,
        'booking_income': bookings.filter(payment_status='paid').aggregate(total=Sum('amount')).get('total') or 0,
        'today_signups': users.filter(created_at__date=today).count(),
    }

    recent_users = users[:8]
    recent_payments = payments.select_related('user', 'business')[:8]
    tickets = SupportTicket.objects.select_related('user')[:8]

    return render(request, 'accounts/platform_admin/dashboard.html', {
        'metrics': metrics,
        'recent_users': recent_users,
        'recent_payments': recent_payments,
        'tickets': tickets,
        'page': 'platform_dashboard',
    })


@staff_required
def platform_admin_users(request):
    status = request.GET.get('status')
    users = CustomUser.objects.all().order_by('-created_at')
    if status:
        users = users.filter(account_status=status)
    return render(request, 'accounts/platform_admin/users.html', {
        'managed_users': users,
        'status': status,
        'page': 'platform_users',
    })


@staff_required
def platform_admin_user_detail(request, user_id):
    from bookings.models import Booking
    from businesses.models import Business
    from payments.models import SubscriptionPayment

    managed_user = get_object_or_404(CustomUser, pk=user_id)
    form = AdminUserForm(request.POST or None, instance=managed_user)
    password_form = AdminPasswordResetForm(request.POST or None, prefix='reset')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'save' and form.is_valid():
            form.save()
            messages.success(request, 'User account updated.')
            return redirect('accounts:platform_user_detail', user_id=managed_user.pk)
        if action == 'reset_password' and password_form.is_valid():
            managed_user.set_password(password_form.cleaned_data['new_password'])
            managed_user.save(update_fields=['password'])
            messages.success(request, 'Password reset successfully.')
            return redirect('accounts:platform_user_detail', user_id=managed_user.pk)

    businesses = Business.objects.filter(pk__in=managed_user.businesses or [])
    bookings = Booking.objects.filter(business__in=businesses).select_related('business', 'service', 'staff').order_by('-date', '-start_time')[:25]
    payments = SubscriptionPayment.objects.filter(user=managed_user).select_related('business')[:25]

    return render(request, 'accounts/platform_admin/user_detail.html', {
        'managed_user': managed_user,
        'form': form,
        'password_form': password_form,
        'businesses': businesses,
        'bookings': bookings,
        'payments': payments,
        'page': 'platform_users',
    })


@staff_required
@require_POST
def platform_admin_user_action(request, user_id):
    managed_user = get_object_or_404(CustomUser, pk=user_id)
    action = request.POST.get('action')
    if action in ('approved', 'rejected', 'suspended', 'pending'):
        managed_user.account_status = action
        managed_user.is_active = action != 'suspended'
        managed_user.save(update_fields=['account_status', 'is_active'])
        messages.success(request, f'Account marked as {action}.')
    return redirect(request.POST.get('next') or 'accounts:platform_users')


@staff_required
def platform_admin_payments(request):
    from payments.models import SubscriptionPayment

    payments = SubscriptionPayment.objects.select_related('user', 'business').all()
    return render(request, 'accounts/platform_admin/payments.html', {
        'payments': payments,
        'page': 'platform_payments',
    })


@staff_required
def platform_admin_payment_detail(request, payment_id):
    from payments.forms import SubscriptionPaymentForm
    from payments.models import SubscriptionPayment

    payment = get_object_or_404(SubscriptionPayment, pk=payment_id)
    form = SubscriptionPaymentForm(request.POST or None, instance=payment)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Payment record updated.')
        return redirect('accounts:platform_payment_detail', payment_id=payment.pk)
    return render(request, 'accounts/platform_admin/payment_detail.html', {
        'payment': payment,
        'form': form,
        'page': 'platform_payments',
    })


@staff_required
def platform_admin_support(request):
    tickets = SupportTicket.objects.select_related('user').all()
    return render(request, 'accounts/platform_admin/support.html', {
        'tickets': tickets,
        'page': 'platform_support',
    })


@staff_required
def platform_admin_ticket_detail(request, ticket_id):
    ticket = get_object_or_404(SupportTicket.objects.select_related('user'), pk=ticket_id)
    form = AdminSupportTicketForm(request.POST or None, instance=ticket)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Support ticket updated.')
        return redirect('accounts:platform_ticket_detail', ticket_id=ticket.pk)
    return render(request, 'accounts/platform_admin/ticket_detail.html', {
        'ticket': ticket,
        'form': form,
        'page': 'platform_support',
    })


@staff_required
def platform_admin_settings(request):
    setting = None
    setting_id = request.GET.get('edit')
    if setting_id:
        setting = get_object_or_404(PlatformSetting, pk=setting_id)

    form = PlatformSettingForm(request.POST or None, instance=setting)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Platform setting saved.')
        return redirect('accounts:platform_settings')

    return render(request, 'accounts/platform_admin/settings.html', {
        'settings_list': PlatformSetting.objects.all(),
        'form': form,
        'editing_setting': setting,
        'page': 'platform_settings',
    })


@staff_required
def platform_admin_user_audience(request, user_id):
    from bookings.models import Booking
    from businesses.models import Business

    managed_user = get_object_or_404(CustomUser, pk=user_id)
    businesses = Business.objects.filter(pk__in=managed_user.businesses or [])
    bookings = Booking.objects.filter(business__in=businesses).select_related('business', 'service').order_by('-date', '-start_time')
    audience_map = {}
    for booking in bookings:
        key = booking.customer_email
        if key not in audience_map:
            audience_map[key] = {
                'name': booking.customer_name,
                'email': booking.customer_email,
                'phone': booking.customer_phone,
                'region': booking.customer_id or booking.business.address or 'Unknown',
                'bookings': 0,
                'last_booking': booking.date,
            }
        audience_map[key]['bookings'] += 1
        if booking.date > audience_map[key]['last_booking']:
            audience_map[key]['last_booking'] = booking.date

    return render(request, 'accounts/platform_admin/audience.html', {
        'managed_user': managed_user,
        'audience': audience_map.values(),
        'page': 'platform_dashboard',
    })
