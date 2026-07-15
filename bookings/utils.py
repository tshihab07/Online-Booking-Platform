from datetime import datetime, timedelta, date, time
from django.db import transaction
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


def get_working_hours(business, weekday_name):
    """Return (open_time, close_time) strings for a given weekday, or None if closed."""
    hours = business.working_hours or {}
    day_data = hours.get(weekday_name.lower())
    if not day_data or not day_data.get('open'):
        return None, None
    return day_data.get('open'), day_data.get('close')


def generate_time_slots(open_str, close_str, duration_minutes=60, buffer_minutes=0):
    """Generate list of (start_time, end_time) tuples for a day - hourly slots."""
    fmt = '%H:%M'
    try:
        open_dt = datetime.strptime(open_str, fmt)
        close_dt = datetime.strptime(close_str, fmt)
    except (ValueError, TypeError):
        return []

    slots = []
    current = open_dt
    # Always use 1-hour intervals for display
    step = timedelta(hours=1)
    end_delta = timedelta(hours=1)

    while current + end_delta <= close_dt:
        slots.append((current.time(), (current + end_delta).time()))
        current += step

    return slots


def get_booked_slots(business, staff, target_date):
    """Return set of (start_time, end_time) tuples already booked."""
    from bookings.models import Booking
    qs = Booking.objects.filter(
        business=business,
        date=target_date,
        status__in=['confirmed', 'in_progress', 'pending'],
    )
    if staff:
        qs = qs.filter(staff=staff)
    return {(b.start_time, b.end_time) for b in qs}


def get_available_slots(business, service, staff, target_date):
    """
    Return list of available slot dicts for a given business/service/staff/date.
    Each dict: {start, end, available: bool}
    Shows hourly slots (9:00, 10:00, etc.) and disables if not enough consecutive hours.
    """
    weekday = target_date.strftime('%A')
    open_str, close_str = get_working_hours(business, weekday)
    if not open_str:
        return []

    # Generate hourly slots (always 1-hour intervals for display)
    all_slots = generate_time_slots(open_str, close_str)
    booked = get_booked_slots(business, staff, target_date)

    # Calculate how many consecutive hours the service needs
    hours_needed = max(1, (service.duration + 59) // 60)  # Round up to hours

    # Enforce lead time
    now = datetime.now()
    lead_hours = business.booking_lead_time or 1
    min_start = now + timedelta(hours=lead_hours)

    result = []
    for start, end in all_slots:
        slot_dt = datetime.combine(target_date, start)
        if target_date == date.today() and slot_dt < min_start:
            continue

        # Check if enough consecutive hours are available for service duration
        available = True
        if hours_needed > 1:
            # Check consecutive hours
            for h in range(hours_needed):
                check_start = (datetime.combine(date.today(), start) + timedelta(hours=h)).time()
                check_end = (datetime.combine(date.today(), start) + timedelta(hours=h+1)).time()
                if (check_start, check_end) in booked:
                    available = False
                    break
        else:
            available = (start, end) not in booked

        result.append({
            'start': start.strftime('%H:%M'),
            'end': end.strftime('%H:%M'),
            'available': available,
        })
    return result


def get_availability_heatmap(business, service, year, month):
    """
    Return dict of {date_str: 'green'|'orange'|'red'|'closed'} for a full month.
    Used for the calendar heatmap display.
    """
    from calendar import monthrange
    from bookings.models import Booking

    _, days_in_month = monthrange(year, month)
    result = {}

    for day in range(1, days_in_month + 1):
        target = date(year, month, day)
        weekday = target.strftime('%A')
        open_str, close_str = get_working_hours(business, weekday)

        if not open_str:
            result[str(target)] = 'closed'
            continue

        # Use hourly slots for heatmap
        all_slots = generate_time_slots(open_str, close_str)
        total = len(all_slots)
        if total == 0:
            result[str(target)] = 'closed'
            continue

        booked_count = Booking.objects.filter(
            business=business,
            date=target,
            status__in=['confirmed', 'in_progress', 'pending'],
        ).count()

        ratio = booked_count / total
        if ratio >= 1.0:
            result[str(target)] = 'red'
        elif ratio >= 0.5:
            result[str(target)] = 'orange'
        else:
            result[str(target)] = 'green'

    return result


def create_booking_atomic(business, service, staff, customer_data, booking_date, start_time_str, payment_method='online'):
    """
    Atomically create a booking with double-booking protection.
    Returns (booking, error_message).
    """
    from bookings.models import Booking
    from platform_admin.plan_limits import check_can_create_booking, record_booking_created

    ok, limit_msg = check_can_create_booking(business)
    if not ok:
        return None, limit_msg

    start_time = datetime.strptime(start_time_str, '%H:%M').time()
    start_dt = datetime.combine(booking_date, start_time)
    end_dt = start_dt + timedelta(minutes=service.duration)
    end_time = end_dt.time()

    # Determine payment status based on payment method
    if payment_method == 'offline':
        payment_status = 'offline_pending'
        status = 'confirmed'  # Booking confirmed but payment pending
    else:
        payment_status = 'unpaid'
        status = 'pending'

    try:
        with transaction.atomic():
            # Double-booking check
            conflict = Booking.objects.filter(
                business=business,
                date=booking_date,
                start_time=start_time,
                status__in=['confirmed', 'in_progress', 'pending'],
            )
            if staff:
                conflict = conflict.filter(staff=staff)

            if conflict.exists():
                return None, "This slot was just taken. Please choose another time."

            booking = Booking.objects.create(
                business=business,
                service=service,
                staff=staff,
                date=booking_date,
                start_time=start_time,
                end_time=end_time,
                amount=service.price,
                status=status,
                payment_method=payment_method,
                payment_status=payment_status,
                **customer_data,
            )
            record_booking_created(business)
            return booking, None

    except Exception as e:
        logger.error(f"Booking creation failed: {e}")
        return None, "An error occurred. Please try again."


def get_recent_bookings_feed(business, limit=10):
    """Return anonymized recent bookings for the social proof ticker."""
    from bookings.models import Booking
    bookings = Booking.objects.filter(
        business=business,
        status__in=['confirmed', 'completed'],
    ).order_by('-created_at')[:limit]

    feed = []
    for b in bookings:
        name_parts = b.customer_name.split()
        anon_name = f"{name_parts[0]} {name_parts[-1][0]}." if len(name_parts) > 1 else name_parts[0]
        delta = timezone.now() - b.created_at
        if delta.seconds < 3600:
            time_ago = f"{delta.seconds // 60} minutes ago"
        elif delta.days == 0:
            time_ago = f"{delta.seconds // 3600} hours ago"
        else:
            time_ago = f"{delta.days} days ago"
        feed.append({
            'name': anon_name,
            'service': b.service.name,
            'time_ago': time_ago,
        })
    return feed
