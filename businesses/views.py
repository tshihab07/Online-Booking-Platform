import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.utils.text import slugify
from django.utils import timezone

from .models import Business, Service, Staff
from .forms import DAYS, OnboardingForm, BusinessSettingsForm, ServiceForm, StaffForm
from .utils import get_dashboard_metrics, get_client_ltv, find_gap_slots
from themes.theme_utils import get_themes_for_type, render_css_vars
from platform_admin.plan_limits import (
    check_can_add_business,
    check_can_add_service,
    check_can_add_staff,
    check_analytics_enabled,
    check_custom_themes,
    get_plan_for_business,
    get_plan_for_user,
)


def _get_active_business(request):
    """Helper: get the active business for the logged-in user."""
    user = request.user
    active_id = user.active_business_id
    if active_id:
        biz = Business.objects.filter(pk=active_id).first()
        if biz:
            return biz
    # Fall back to first business
    ids = user.businesses or []
    if ids:
        return Business.objects.filter(pk__in=ids).first()
    return None


# ─── Onboarding ──────────────────────────────────────────────────────────────

@login_required
def onboarding(request):
    form = OnboardingForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        allowed, msg = check_can_add_business(request.user)
        if not allowed:
            messages.error(request, msg)
            return render(request, 'businesses/onboarding.html', {'form': form})

        business = form.save(commit=False)
        base_slug = slugify(business.name)
        slug = base_slug
        counter = 1
        while Business.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        business.slug = slug
        business.plan = get_plan_for_user(request.user).tier

        # Default working hours Mon–Fri 9–17
        business.working_hours = {
            day: {'open': '09:00', 'close': '17:00', 'closed': False}
            for day in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
        }
        business.working_hours.update({
            'saturday': {'open': '10:00', 'close': '14:00', 'closed': False},
            'sunday': {'open': '', 'close': '', 'closed': True},
        })
        business.save()

        # Link business to user
        user = request.user
        biz_list = user.businesses or []
        biz_list.append(str(business.pk))
        user.businesses = biz_list
        user.active_business_id = str(business.pk)
        user.save(update_fields=['businesses', 'active_business_id'])

        messages.success(request, f'"{business.name}" created! Now add your services.')
        return redirect('businesses:services')

    return render(request, 'businesses/onboarding.html', {'form': form})


# ─── Dashboard ───────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    business = _get_active_business(request)
    if not business:
        return redirect('businesses:onboarding')

    metrics = get_dashboard_metrics(business)
    return render(request, 'businesses/dashboard.html', {
        'business': business,
        'metrics': metrics,
        'page': 'dashboard',
    })


# ─── Calendar ────────────────────────────────────────────────────────────────

@login_required
def calendar_view(request):
    business = _get_active_business(request)
    if not business:
        return redirect('businesses:onboarding')

    from bookings.models import Booking
    from datetime import date
    today = date.today()

    bookings = Booking.objects.filter(
        business=business,
        date=today,
    ).order_by('start_time').select_related('service', 'staff')

    staff_list = Staff.objects.filter(business=business, is_active=True)

    return render(request, 'businesses/calendar.html', {
        'business': business,
        'bookings': bookings,
        'staff_list': staff_list,
        'today': today,
        'page': 'calendar',
    })


@login_required
def all_time_bookings(request):
    business = _get_active_business(request)
    if not business:
        return redirect('businesses:onboarding')

    from bookings.models import Booking
    bookings = Booking.objects.filter(business=business).select_related(
        'service', 'staff'
    ).order_by('-date', '-start_time')

    status = request.GET.get('status')
    if status:
        bookings = bookings.filter(status=status)

    return render(request, 'businesses/all_time_bookings.html', {
        'business': business,
        'bookings': bookings,
        'status': status,
        'statuses': Booking.STATUS_CHOICES,
        'page': 'all_bookings',
    })


@login_required
def calendar_bookings_api(request):
    """JSON endpoint for calendar: returns bookings for a date range."""
    business = _get_active_business(request)
    if not business:
        return JsonResponse({'error': 'No business'}, status=400)

    from bookings.models import Booking
    from datetime import date
    start_str = request.GET.get('start', str(date.today()))
    end_str = request.GET.get('end', str(date.today()))

    try:
        from datetime import datetime
        start = datetime.strptime(start_str[:10], '%Y-%m-%d').date()
        end = datetime.strptime(end_str[:10], '%Y-%m-%d').date()
    except ValueError:
        start = end = date.today()

    bookings = Booking.objects.filter(
        business=business,
        date__range=(start, end),
    ).select_related('service', 'staff')

    STATUS_COLORS = {
        'confirmed': '#22c55e',
        'pending': '#f59e0b',
        'in_progress': '#3b82f6',
        'completed': '#6366f1',
        'cancelled': '#ef4444',
        'no_show': '#dc2626',
    }

    events = []
    for b in bookings:
        events.append({
            'id': str(b.pk),
            'title': f"{b.customer_name} — {b.service.name}",
            'start': f"{b.date}T{b.start_time}",
            'end': f"{b.date}T{b.end_time}",
            'color': STATUS_COLORS.get(b.status, '#6366f1'),
            'extendedProps': {
                'status': b.status,
                'staff': b.staff.name if b.staff else 'Any',
                'customer_email': b.customer_email,
                'customer_phone': b.customer_phone,
                'amount': str(b.amount),
                'payment_status': b.payment_status,
            },
        })
    return JsonResponse(events, safe=False)


@login_required
@require_POST
def update_booking_status(request, booking_id):
    from bookings.models import Booking
    business = _get_active_business(request)
    booking = get_object_or_404(Booking, pk=booking_id, business=business)
    new_status = request.POST.get('status')
    valid = [s[0] for s in Booking.STATUS_CHOICES]
    if new_status in valid:
        booking.status = new_status
        booking.save(update_fields=['status'])
        return JsonResponse({'success': True, 'status': new_status})
    return JsonResponse({'error': 'Invalid status'}, status=400)


# ─── Services ────────────────────────────────────────────────────────────────

@login_required
def services_view(request):
    business = _get_active_business(request)
    if not business:
        return redirect('businesses:onboarding')
    services = Service.objects.filter(business=business).order_by('category', 'name')
    return render(request, 'businesses/services.html', {
        'business': business,
        'services': services,
        'page': 'services',
    })


@login_required
def service_create(request):
    business = _get_active_business(request)
    if not business:
        return redirect('businesses:onboarding')
    form = ServiceForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        allowed, msg = check_can_add_service(business)
        if not allowed:
            messages.error(request, msg)
            return render(request, 'businesses/service_form.html', {
                'form': form, 'business': business, 'action': 'Add', 'page': 'services',
            })
        service = form.save(commit=False)
        service.business = business
        service.save()
        messages.success(request, f'Service "{service.name}" added.')
        return redirect('businesses:services')
    return render(request, 'businesses/service_form.html', {
        'form': form, 'business': business, 'action': 'Add', 'page': 'services',
    })


@login_required
def service_edit(request, service_id):
    business = _get_active_business(request)
    service = get_object_or_404(Service, pk=service_id, business=business)
    form = ServiceForm(request.POST or None, request.FILES or None, instance=service)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Service updated.')
        return redirect('businesses:services')
    return render(request, 'businesses/service_form.html', {
        'form': form, 'business': business, 'action': 'Edit', 'page': 'services',
    })


@login_required
@require_POST
def service_delete(request, service_id):
    business = _get_active_business(request)
    service = get_object_or_404(Service, pk=service_id, business=business)
    service.delete()
    messages.success(request, 'Service deleted.')
    return redirect('businesses:services')


# ─── Staff ───────────────────────────────────────────────────────────────────

@login_required
def staff_view(request):
    business = _get_active_business(request)
    if not business:
        return redirect('businesses:onboarding')
    staff_list = Staff.objects.filter(business=business).order_by('name')
    return render(request, 'businesses/staff.html', {
        'business': business,
        'staff_list': staff_list,
        'page': 'staff',
    })


@login_required
def staff_create(request):
    business = _get_active_business(request)
    if not business:
        return redirect('businesses:onboarding')
    form = StaffForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        allowed, msg = check_can_add_staff(business)
        if not allowed:
            messages.error(request, msg)
            return render(request, 'businesses/staff_form.html', {
                'form': form, 'business': business, 'action': 'Add', 'page': 'staff',
            })
        staff = form.save(commit=False)
        staff.business = business
        staff.save()
        messages.success(request, f'Staff member "{staff.name}" added.')
        return redirect('businesses:staff')
    return render(request, 'businesses/staff_form.html', {
        'form': form, 'business': business, 'action': 'Add', 'page': 'staff',
    })


@login_required
def staff_edit(request, staff_id):
    business = _get_active_business(request)
    staff = get_object_or_404(Staff, pk=staff_id, business=business)
    form = StaffForm(request.POST or None, request.FILES or None, instance=staff)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Staff member updated.')
        return redirect('businesses:staff')
    return render(request, 'businesses/staff_form.html', {
        'form': form, 'business': business, 'action': 'Edit', 'page': 'staff',
    })


@login_required
@require_POST
def staff_delete(request, staff_id):
    business = _get_active_business(request)
    staff = get_object_or_404(Staff, pk=staff_id, business=business)
    staff.delete()
    messages.success(request, 'Staff member removed.')
    return redirect('businesses:staff')


# ─── Settings / Site Builder ─────────────────────────────────────────────────

@login_required
def settings_view(request):
    business = _get_active_business(request)
    if not business:
        return redirect('businesses:onboarding')

    form = BusinessSettingsForm(request.POST or None, request.FILES or None, instance=business)
    themes = get_themes_for_type(business.business_type)
    plan = get_plan_for_business(business)

    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Settings saved.')
        return redirect('businesses:settings')

    return render(request, 'businesses/settings.html', {
        'business': business,
        'form': form,
        'themes': themes,
        'plan': plan,
        'days': DAYS,
        'page': 'settings',
    })


@login_required
@require_POST
def update_theme(request):
    business = _get_active_business(request)
    if not business:
        return JsonResponse({'error': 'No business'}, status=400)

    theme_key = request.POST.get('theme')
    allowed, msg = check_custom_themes(business)
    if not allowed:
        return JsonResponse({'error': msg}, status=403)
    themes_dict = dict(get_themes_for_type(business.business_type))
    if theme_key in themes_dict:
        business.theme = theme_key
        business.save(update_fields=['theme'])
        return JsonResponse({'success': True, 'css': render_css_vars(business)})
    return JsonResponse({'error': 'Invalid theme'}, status=400)


@login_required
@require_POST
def update_brand_colors(request):
    business = _get_active_business(request)
    if not business:
        return JsonResponse({'error': 'No business'}, status=400)

    try:
        data = json.loads(request.body)
        colors = {k: v for k, v in data.items() if k in ('primary', 'secondary', 'accent')}
        business.brand_colors = colors
        business.save(update_fields=['brand_colors'])
        return JsonResponse({'success': True, 'css': render_css_vars(business)})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@login_required
@require_POST
def update_working_hours(request):
    business = _get_active_business(request)
    if not business:
        return JsonResponse({'error': 'No business'}, status=400)

    try:
        data = json.loads(request.body)
        business.working_hours = data
        business.save(update_fields=['working_hours'])
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ─── CRM / Clients ───────────────────────────────────────────────────────────

@login_required
def clients_view(request):
    business = _get_active_business(request)
    if not business:
        return redirect('businesses:onboarding')

    from bookings.models import Booking
    from django.db.models import Count, Sum, Max

    # Aggregate unique customers
    raw = (
        Booking.objects
        .filter(business=business)
        .values('customer_email', 'customer_name', 'customer_phone')
        .annotate(
            visit_count=Count('pk'),
            last_visit=Max('date'),
        )
        .order_by('-last_visit')
    )

    clients = []
    for c in raw:
        ltv_data = get_client_ltv(business, c['customer_email'])
        clients.append({**c, **ltv_data})

    return render(request, 'businesses/clients.html', {
        'business': business,
        'clients': clients,
        'page': 'clients',
    })


@login_required
def client_detail(request, email):
    business = _get_active_business(request)
    if not business:
        return redirect('businesses:onboarding')

    from bookings.models import Booking
    bookings = Booking.objects.filter(
        business=business,
        customer_email=email,
    ).order_by('-date').select_related('service', 'staff')

    ltv_data = get_client_ltv(business, email)
    customer_name = bookings.first().customer_name if bookings.exists() else email

    return render(request, 'businesses/client_detail.html', {
        'business': business,
        'customer_email': email,
        'customer_name': customer_name,
        'bookings': bookings,
        'ltv_data': ltv_data,
        'page': 'clients',
    })


# ─── Analytics ───────────────────────────────────────────────────────────────

@login_required
def analytics_view(request):
    business = _get_active_business(request)
    if not business:
        return redirect('businesses:onboarding')

    allowed, msg = check_analytics_enabled(business)
    if not allowed:
        messages.warning(request, msg)
        return redirect('businesses:dashboard')

    from bookings.models import Booking
    from datetime import date, timedelta

    today = date.today()
    last_30 = today - timedelta(days=30)

    bookings_30 = Booking.objects.filter(business=business, date__gte=last_30)

    # Revenue by day (last 7 days)
    revenue_by_day = {}
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        rev = sum(
            b.amount for b in bookings_30.filter(date=d, status='completed')
        )
        revenue_by_day[str(d)] = float(rev)

    # Bookings by service
    from django.db.models import Count
    by_service = list(
        bookings_30.values('service__name').annotate(count=Count('pk')).order_by('-count')[:8]
    )

    # Status breakdown
    status_counts = {}
    for s, _ in Booking.STATUS_CHOICES:
        status_counts[s] = bookings_30.filter(status=s).count()

    return render(request, 'businesses/analytics.html', {
        'business': business,
        'revenue_by_day': json.dumps(revenue_by_day),
        'by_service': json.dumps([{'name': x['service__name'], 'count': x['count']} for x in by_service]),
        'status_counts': json.dumps(status_counts),
        'page': 'analytics',
    })


# ─── Fill the Gap Campaign ────────────────────────────────────────────────────

@login_required
def fill_gap_view(request):
    business = _get_active_business(request)
    if not business:
        return redirect('businesses:onboarding')

    gaps = find_gap_slots(business, days_ahead=3)

    if request.method == 'POST':
        # Send rebook emails to recent customers
        from bookings.models import Booking
        from notifications.utils import send_rebook_magic_link
        from django.conf import settings

        recent_emails = list(
            Booking.objects.filter(business=business, status='completed')
            .values_list('customer_email', flat=True)
            .distinct()[:50]
        )
        base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
        rebook_url = f"{base_url}/b/{business.slug}/"

        sent = 0
        for email in recent_emails:
            last_booking = Booking.objects.filter(
                business=business, customer_email=email
            ).order_by('-date').first()
            if last_booking:
                try:
                    send_rebook_magic_link(last_booking, rebook_url)
                    sent += 1
                except Exception:
                    pass

        messages.success(request, f'Re-engagement emails sent to {sent} customers.')
        return redirect('businesses:fill_gap')

    return render(request, 'businesses/fill_gap.html', {
        'business': business,
        'gaps': gaps,
        'page': 'marketing',
    })
