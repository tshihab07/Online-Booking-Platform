from django.utils import timezone
from datetime import timedelta, date
from decimal import Decimal


def get_dashboard_metrics(business):
    """Compute KPI metrics for the dashboard cockpit."""
    from bookings.models import Booking

    today = date.today()
    yesterday = today - timedelta(days=1)

    base_qs = Booking.objects.filter(business=business)

    # Revenue today vs yesterday
    today_revenue = sum(
        b.amount for b in base_qs.filter(date=today, status='completed')
    ) or Decimal('0')
    yesterday_revenue = sum(
        b.amount for b in base_qs.filter(date=yesterday, status='completed')
    ) or Decimal('0')

    revenue_delta = today_revenue - yesterday_revenue
    revenue_trend = 'up' if revenue_delta >= 0 else 'down'

    # Completion rate (last 30 days)
    thirty_days_ago = today - timedelta(days=30)
    recent = base_qs.filter(date__gte=thirty_days_ago)
    total_recent = recent.count()
    completed_recent = recent.filter(status='completed').count()
    completion_rate = round((completed_recent / total_recent * 100) if total_recent else 0, 1)

    # New vs returning customers
    all_emails = list(base_qs.values_list('customer_email', flat=True))
    unique_emails = set(all_emails)
    returning = sum(1 for e in unique_emails if all_emails.count(e) > 1)
    new_customers = len(unique_emails) - returning

    # Today's queue
    todays_bookings = list(
        base_qs.filter(date=today)
        .exclude(status__in=['cancelled', 'no_show'])
        .order_by('start_time')
        .select_related('service', 'staff')
    )

    # No-show count
    no_show_count = base_qs.filter(date=today, status='no_show').count()

    return {
        'today_revenue': today_revenue,
        'yesterday_revenue': yesterday_revenue,
        'revenue_delta': abs(revenue_delta),
        'revenue_trend': revenue_trend,
        'completion_rate': completion_rate,
        'new_customers': new_customers,
        'returning_customers': returning,
        'todays_bookings': todays_bookings,
        'no_show_count': no_show_count,
        'total_bookings_today': len(todays_bookings),
    }


def get_client_ltv(business, customer_email):
    """Calculate lifetime value for a single customer."""
    from bookings.models import Booking
    bookings = Booking.objects.filter(
        business=business,
        customer_email=customer_email,
        status='completed',
    )
    total = sum(b.amount for b in bookings) or Decimal('0')
    count = bookings.count()
    last = bookings.order_by('-date').first()
    return {
        'ltv': total,
        'visit_count': count,
        'last_visit': last.date if last else None,
        'last_service': last.service.name if last else None,
    }


def find_gap_slots(business, days_ahead=3):
    """Find empty slots in the next N days for 'Fill the Gap' campaigns."""
    from bookings.models import Booking
    from bookings.utils import get_working_hours, generate_time_slots, get_booked_slots

    gaps = []
    today = date.today()

    for i in range(1, days_ahead + 1):
        target = today + timedelta(days=i)
        weekday = target.strftime('%A')
        open_str, close_str = get_working_hours(business, weekday)
        if not open_str:
            continue

        # Use first active service as reference duration
        from businesses.models import Service
        service = Service.objects.filter(business=business, is_active=True).first()
        if not service:
            continue

        all_slots = generate_time_slots(open_str, close_str, service.duration, business.buffer_time or 0)
        booked = get_booked_slots(business, None, target)
        empty = [(s, e) for s, e in all_slots if (s, e) not in booked]

        if empty:
            gaps.append({'date': target, 'empty_slots': len(empty), 'slots': empty[:3]})

    return gaps
