from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.db.models import Sum
from django.utils import timezone
from django.core.paginator import Paginator
from django.conf import settings
from functools import wraps

from accounts.models import CustomUser, SupportTicket, PlatformSetting
from businesses.models import Business, Service, Staff
from bookings.models import Booking
from payments.models import SubscriptionPayment
from .models import Plan, Announcement, UserUsage, AuditLog
from .forms import (
    PlanForm, AnnouncementForm,
    UserSearchForm, BusinessSearchForm, BookingFilterForm
)

def _get_audit_admin(request):
    """Return the CustomUser for audit logging, or None if kgb session only."""
    if request.user.is_authenticated:
        return request.user
    return None


KGB_SESSION_KEY = '_kgb_admin_authenticated'
def kgb_admin_required(view_func):
    """Decorator: requires active KGB admin session (ADMIN_USERNAME/ADMIN_PASSWORD)."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get(KGB_SESSION_KEY):
            return redirect('platform_admin:login')
        return view_func(request, *args, **kwargs)
    return wrapper


def platform_admin_login_view(request):
    """Login for /kgb-admin/ using ADMIN_USERNAME + ADMIN_PASSWORD from .env."""
    if request.session.get(KGB_SESSION_KEY):
        return redirect('platform_admin:dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        admin_username = settings.PLATFORM_ADMIN_USERNAME
        admin_password = settings.PLATFORM_ADMIN_PASSWORD

        if username == admin_username and password == admin_password:
            request.session[KGB_SESSION_KEY] = True
            request.session['kgb_admin_username'] = username
            request.session.set_expiry(28800)  # 8 hours
            return redirect('platform_admin:dashboard')
        else:
            error = 'Invalid credentials.'

    return render(request, 'platform_admin/login.html', {'error': error})


def platform_admin_logout_view(request):
    """Clear KGB admin session."""
    request.session.pop(KGB_SESSION_KEY, None)
    request.session.pop('kgb_admin_username', None)
    return redirect('platform_admin:login')


@kgb_admin_required
def dashboard(request):
    """Main admin dashboard"""
    today = timezone.localdate()
    month_start = today.replace(day=1)
    
    # Quick metrics
    metrics = {
        'total_users': CustomUser.objects.count(),
        'active_users': CustomUser.objects.filter(is_active=True, account_status='approved').count(),
        'pending_users': CustomUser.objects.filter(account_status='pending').count(),
        'suspended_users': CustomUser.objects.filter(account_status='suspended').count(),
        'total_businesses': Business.objects.count(),
        'active_businesses': Business.objects.filter(is_active=True).count(),
        'total_bookings': Booking.objects.count(),
        'month_bookings': Booking.objects.filter(date__gte=month_start).count(),
        'total_revenue': SubscriptionPayment.objects.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0,
        'month_revenue': SubscriptionPayment.objects.filter(status='paid', created_at__date__gte=month_start).aggregate(total=Sum('amount'))['total'] or 0,
        'open_tickets': SupportTicket.objects.exclude(status__in=['resolved', 'closed']).count(),
        'today_signups': CustomUser.objects.filter(created_at__date=today).count(),
    }
    
    # Plan distribution
    plan_distribution = {}
    for plan in Plan.objects.filter(is_active=True):
        plan_distribution[plan.tier] = Business.objects.filter(plan=plan.tier).count()
    
    # Recent activity
    recent_users = CustomUser.objects.order_by('-created_at')[:5]
    recent_bookings = Booking.objects.select_related('business', 'service').order_by('-created_at')[:5]
    recent_payments = SubscriptionPayment.objects.select_related('user', 'business').order_by('-created_at')[:5]
    
    # Active announcements
    active_announcements = Announcement.objects.filter(status='published').order_by('-published_at')[:3]
    
    # Recent audit logs
    recent_logs = AuditLog.objects.select_related('admin_user', 'target_user')[:10]
    
    context = {
        'metrics': metrics,
        'plan_distribution': plan_distribution,
        'recent_users': recent_users,
        'recent_bookings': recent_bookings,
        'recent_payments': recent_payments,
        'active_announcements': active_announcements,
        'recent_logs': recent_logs,
        'page': 'dashboard',
    }
    return render(request, 'platform_admin/dashboard.html', context)


@kgb_admin_required
def user_list(request):
    """List all users with search and filters"""
    form = UserSearchForm(request.GET)
    users = CustomUser.objects.all().order_by('-created_at')
    
    if form.is_valid():
        search = form.cleaned_data.get('search')
        status = form.cleaned_data.get('status')
        plan = form.cleaned_data.get('plan')
        
        if search:
            users = users.filter(email__icontains=search) | users.filter(first_name__icontains=search) | users.filter(last_name__icontains=search)
        if status:
            users = users.filter(account_status=status)
        if plan:
            # Get businesses on this plan, then their users
            business_ids = Business.objects.filter(plan=plan).values_list('pk', flat=True)
            users = users.filter(businesses__overlap=list(business_ids))
    
    paginator = Paginator(users, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'platform_admin/users.html', {
        'page_obj': page_obj,
        'form': form,
        'page': 'users',
    })


@kgb_admin_required
def user_detail(request, user_id):
    """View and manage a user"""
    target_user = get_object_or_404(CustomUser, pk=user_id)
    
    # Get user's businesses
    businesses = Business.objects.filter(pk__in=target_user.businesses or [])
    
    # Get usage
    usage, _ = UserUsage.objects.get_or_create(user=target_user)
    
    # Get recent bookings across all businesses
    bookings = Booking.objects.filter(business__in=businesses).select_related('business', 'service')[:20]
    
    # Get payments
    payments = SubscriptionPayment.objects.filter(user=target_user)[:20]
    
    # Get tickets
    tickets = SupportTicket.objects.filter(user=target_user)[:10]
    
    if request.method == 'POST':
        action = request.POST.get('action')
        note = request.POST.get('admin_notes', '')
        
        if action == 'delete':
            email = target_user.email
            AuditLog.objects.create(
                admin_user=_get_audit_admin(request),
                action='user_delete',
                target_user=target_user,
                details={'email': email, 'note': note},
                ip_address=request.META.get('REMOTE_ADDR'),
            )
            target_user.delete()
            messages.success(request, f'User {email} deleted.')
            return redirect('platform_admin:users')

        if action in ('approve', 'suspend', 'reject', 'pending'):
            old_status = target_user.account_status
            target_user.account_status = 'approved' if action == 'approve' else action
            target_user.is_active = action == 'approve'
            if note:
                target_user.admin_notes = note
            target_user.save()
            
            audit_action = 'user_activate' if action == 'approve' else (
                f'user_{action}' if f'user_{action}' in dict(AuditLog.ACTION_CHOICES) else 'user_update'
            )
            AuditLog.objects.create(
                admin_user=_get_audit_admin(request),
                action=audit_action,
                target_user=target_user,
                details={'old_status': old_status, 'new_status': action, 'note': note},
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, f'User status changed to {action}.')
            return redirect('platform_admin:user_detail', user_id=user_id)
    
    return render(request, 'platform_admin/user_detail.html', {
        'target_user': target_user,
        'businesses': businesses,
        'usage': usage,
        'bookings': bookings,
        'payments': payments,
        'tickets': tickets,
        'page': 'users',
    })


@kgb_admin_required
@require_POST
def user_change_plan(request, user_id):
    """Change user's plan"""
    target_user = get_object_or_404(CustomUser, pk=user_id)
    new_plan = request.POST.get('plan')
    
    if new_plan:
        # Update all businesses for this user
        Business.objects.filter(pk__in=target_user.businesses or []).update(plan=new_plan)
        
        AuditLog.objects.create(
            admin_user=_get_audit_admin(request),
            action='plan_change',
            target_user=target_user,
            details={'new_plan': new_plan},
            ip_address=request.META.get('REMOTE_ADDR')
        )
        messages.success(request, f'Plan changed to {new_plan}.')
    
    return redirect('platform_admin:user_detail', user_id=user_id)


@kgb_admin_required
def business_list(request):
    """List all businesses"""
    form = BusinessSearchForm(request.GET)
    businesses = Business.objects.all().order_by('-created_at')
    
    if form.is_valid():
        search = form.cleaned_data.get('search')
        business_type = form.cleaned_data.get('business_type')
        status = form.cleaned_data.get('status')
        
        if search:
            businesses = businesses.filter(name__icontains=search) | businesses.filter(slug__icontains=search)
        if business_type:
            businesses = businesses.filter(business_type=business_type)
        if status == 'active':
            businesses = businesses.filter(is_active=True)
        elif status == 'inactive':
            businesses = businesses.filter(is_active=False)
    
    paginator = Paginator(businesses, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'platform_admin/businesses.html', {
        'page_obj': page_obj,
        'form': form,
        'page': 'businesses',
    })


@kgb_admin_required
def business_detail(request, business_id):
    """View and manage a business"""
    business = get_object_or_404(Business, pk=business_id)
    
    services = Service.objects.filter(business=business)
    staff = Staff.objects.filter(business=business)
    bookings = Booking.objects.filter(business=business).select_related('service', 'staff')[:30]
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'deactivate':
            business.is_active = False
            business.save()
            AuditLog.objects.create(
                admin_user=_get_audit_admin(request),
                action='business_deactivate',
                target_business_id=str(business.pk),
                details={'business_name': business.name},
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, 'Business deactivated.')
        elif action == 'activate':
            business.is_active = True
            business.save()
            AuditLog.objects.create(
                admin_user=_get_audit_admin(request),
                action='business_activate',
                target_business_id=str(business.pk),
                details={'business_name': business.name},
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, 'Business activated.')
        
        return redirect('platform_admin:business_detail', business_id=business_id)
    
    owner = CustomUser.objects.filter(businesses__overlap=[str(business.pk)]).first()

    return render(request, 'platform_admin/business_detail.html', {
        'business': business,
        'services': services,
        'staff': staff,
        'bookings': bookings,
        'owner': owner,
        'page': 'businesses',
    })


@kgb_admin_required
def booking_list(request):
    """List all bookings across all tenants"""
    form = BookingFilterForm(request.GET)
    bookings = Booking.objects.select_related('business', 'service', 'staff').all().order_by('-date', '-start_time')
    
    if form.is_valid():
        search = form.cleaned_data.get('search')
        status = form.cleaned_data.get('status')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if search:
            bookings = bookings.filter(customer_email__icontains=search) | bookings.filter(customer_name__icontains=search)
        if status:
            bookings = bookings.filter(status=status)
        if date_from:
            bookings = bookings.filter(date__gte=date_from)
        if date_to:
            bookings = bookings.filter(date__lte=date_to)
    
    paginator = Paginator(bookings, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'platform_admin/bookings.html', {
        'page_obj': page_obj,
        'form': form,
        'page': 'bookings',
    })


@kgb_admin_required
def payment_list(request):
    """List all payments"""
    payments = SubscriptionPayment.objects.select_related('user', 'business').all().order_by('-created_at')
    
    status = request.GET.get('status')
    if status:
        payments = payments.filter(status=status)
    
    paginator = Paginator(payments, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'platform_admin/payments.html', {
        'page_obj': page_obj,
        'status': status,
        'page': 'payments',
    })


@kgb_admin_required
def payment_detail(request, payment_id):
    """View payment details"""
    payment = get_object_or_404(SubscriptionPayment.objects.select_related('user', 'business'), pk=payment_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'refund':
            payment.status = 'refunded'
            payment.save()
            AuditLog.objects.create(
                admin_user=_get_audit_admin(request),
                action='payment_refund',
                target_user=payment.user,
                details={'payment_id': str(payment.pk), 'amount': str(payment.amount)},
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, 'Payment marked as refunded.')
            return redirect('platform_admin:payment_detail', payment_id=payment_id)
    
    return render(request, 'platform_admin/payment_detail.html', {
        'payment': payment,
        'page': 'payments',
    })


@kgb_admin_required
def support_list(request):
    """List all support tickets"""
    tickets = SupportTicket.objects.select_related('user').all().order_by('-created_at')
    
    status = request.GET.get('status')
    if status:
        tickets = tickets.filter(status=status)
    
    paginator = Paginator(tickets, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'platform_admin/support.html', {
        'page_obj': page_obj,
        'status': status,
        'page': 'support',
    })


@kgb_admin_required
def support_detail(request, ticket_id):
    """View and respond to support ticket"""
    ticket = get_object_or_404(SupportTicket.objects.select_related('user'), pk=ticket_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        response = request.POST.get('admin_response', '')
        new_status = request.POST.get('status')
        
        if action == 'respond':
            ticket.admin_response = response
            ticket.status = new_status or ticket.status
            ticket.save()
            
            if ticket.status in ['resolved', 'closed']:
                AuditLog.objects.create(
                    admin_user=_get_audit_admin(request),
                    action='ticket_resolve',
                    target_user=ticket.user,
                    details={'ticket_id': str(ticket.pk), 'subject': ticket.subject},
                    ip_address=request.META.get('REMOTE_ADDR')
                )
            
            messages.success(request, 'Response saved.')
            return redirect('platform_admin:support_detail', ticket_id=ticket_id)
    
    return render(request, 'platform_admin/support_detail.html', {
        'ticket': ticket,
        'page': 'support',
    })


@kgb_admin_required
def plan_list(request):
    """List and manage plans"""
    plans = Plan.objects.all()
    
    if request.method == 'POST':
        form = PlanForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Plan created.')
            return redirect('platform_admin:plans')
    else:
        form = PlanForm()
    
    return render(request, 'platform_admin/plans.html', {
        'plans': plans,
        'form': form,
        'page': 'plans',
    })


@kgb_admin_required
def plan_edit(request, plan_id):
    """Edit a plan"""
    plan = get_object_or_404(Plan, pk=plan_id)
    
    if request.method == 'POST':
        form = PlanForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, 'Plan updated.')
            return redirect('platform_admin:plans')
    else:
        form = PlanForm(instance=plan)
    
    return render(request, 'platform_admin/plan_form.html', {
        'form': form,
        'plan': plan,
        'page': 'plans',
    })


@kgb_admin_required
def announcement_list(request):
    """List and manage announcements"""
    announcements = Announcement.objects.select_related('created_by').all()
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = _get_audit_admin(request)
            if announcement.status == 'published' and not announcement.published_at:
                announcement.published_at = timezone.now()
            announcement.save()
            messages.success(request, 'Announcement created.')
            return redirect('platform_admin:announcements')
    else:
        form = AnnouncementForm()
    
    return render(request, 'platform_admin/announcements.html', {
        'announcements': announcements,
        'form': form,
        'page': 'announcements',
    })


@kgb_admin_required
def announcement_edit(request, announcement_id):
    """Edit an announcement"""
    announcement = get_object_or_404(Announcement, pk=announcement_id)
    
    if request.method == 'POST':
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            announcement = form.save()
            if announcement.status == 'published' and not announcement.published_at:
                announcement.published_at = timezone.now()
                announcement.save()
            messages.success(request, 'Announcement updated.')
            return redirect('platform_admin:announcements')
    else:
        form = AnnouncementForm(instance=announcement)
    
    return render(request, 'platform_admin/announcement_form.html', {
        'form': form,
        'announcement': announcement,
        'page': 'announcements',
    })


@kgb_admin_required
def settings_view(request):
    """Platform settings"""
    settings_list = PlatformSetting.objects.all()
    
    if request.method == 'POST':
        key = request.POST.get('key')
        value = request.POST.get('value')
        
        if key:
            setting, _ = PlatformSetting.objects.get_or_create(key=key, defaults={'label': key})
            setting.value = value
            setting.save()
            
            AuditLog.objects.create(
                admin_user=_get_audit_admin(request),
                action='settings_update',
                details={'key': key, 'value': value},
                ip_address=request.META.get('REMOTE_ADDR')
            )
            messages.success(request, 'Setting saved.')
            return redirect('platform_admin:settings')
    
    return render(request, 'platform_admin/settings.html', {
        'settings_list': settings_list,
        'page': 'settings',
    })


@kgb_admin_required
def audit_logs(request):
    """View audit logs"""
    logs = AuditLog.objects.select_related('admin_user', 'target_user').all().order_by('-created_at')
    
    action = request.GET.get('action')
    if action:
        logs = logs.filter(action=action)
    
    paginator = Paginator(logs, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'platform_admin/audit_logs.html', {
        'page_obj': page_obj,
        'action': action,
        'audit_log_action_choices': AuditLog.ACTION_CHOICES,
        'page': 'audit',
    })


@kgb_admin_required
def impersonate_user(request, user_id):
    """Log in as a user to debug their experience (Django auth session)."""
    target_user = get_object_or_404(CustomUser, pk=user_id)
    request.session['_impersonate_kgb'] = True
    login(request, target_user, backend='django.contrib.auth.backends.ModelBackend')
    messages.info(request, f'Impersonating {target_user.email} — go to /kgb-admin/stop-impersonation/ to return.')
    return redirect('businesses:dashboard')


def stop_impersonation(request):
    """End impersonation, clear Django auth session, return to kgb-admin."""
    from django.contrib.auth import logout as auth_logout
    auth_logout(request)
    request.session[KGB_SESSION_KEY] = True
    return redirect('platform_admin:dashboard')
