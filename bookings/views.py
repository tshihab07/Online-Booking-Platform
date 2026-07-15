import json
from datetime import date, datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt

from businesses.models import Business, Service, Staff
from bookings.models import Booking
from bookings.utils import (
    get_available_slots,
    get_availability_heatmap,
    create_booking_atomic,
    get_recent_bookings_feed,
)
from themes.theme_utils import render_css_vars
from notifications.utils import send_booking_confirmation


def public_landing(request, slug, step=1):
    """Public-facing landing page for a business."""
    business = get_object_or_404(Business, slug=slug, is_active=True)
    services = Service.objects.filter(business=business, is_active=True).order_by('category', 'name')
    staff_list = Staff.objects.filter(business=business, is_active=True)
    feed = get_recent_bookings_feed(business, limit=8)
    css_vars = render_css_vars(business)

    # Average rating placeholder (extend with Review model later)
    avg_rating = 4.8
    review_count = Booking.objects.filter(business=business, status='completed').count()

    return render(request, 'bookings/landing.html', {
        'business': business,
        'services': services,
        'staff_list': staff_list,
        'feed': json.dumps(feed),
        'css_vars': css_vars,
        'avg_rating': avg_rating,
        'review_count': review_count,
        'initial_step': step,
    })


@require_GET
def api_availability(request, slug):
    """
    JSON API: returns available time slots.
    Params: service_id, staff_id (optional), date (YYYY-MM-DD)
    """
    business = get_object_or_404(Business, slug=slug, is_active=True)
    service_id = request.GET.get('service_id')
    staff_id = request.GET.get('staff_id')
    date_str = request.GET.get('date')

    if not service_id or not date_str:
        return JsonResponse({'error': 'service_id and date required'}, status=400)

    service = get_object_or_404(Service, pk=service_id, business=business, is_active=True)
    staff = None
    if staff_id:
        staff = Staff.objects.filter(pk=staff_id, business=business, is_active=True).first()

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    slots = get_available_slots(business, service, staff, target_date)
    return JsonResponse({'slots': slots, 'date': date_str})


@require_GET
def api_heatmap(request, slug):
    """
    JSON API: returns availability heatmap for a month.
    Params: service_id, year, month
    """
    business = get_object_or_404(Business, slug=slug, is_active=True)
    service_id = request.GET.get('service_id')
    year = int(request.GET.get('year', date.today().year))
    month = int(request.GET.get('month', date.today().month))

    if not service_id:
        return JsonResponse({'error': 'service_id required'}, status=400)

    service = get_object_or_404(Service, pk=service_id, business=business, is_active=True)
    heatmap = get_availability_heatmap(business, service, year, month)
    return JsonResponse({'heatmap': heatmap})


@require_GET
def api_staff_slots(request, slug):
    """JSON API: returns slots filtered by staff member."""
    return api_availability(request, slug)


@require_POST
def create_booking(request, slug):
    """Step 4: Process booking form submission."""
    business = get_object_or_404(Business, slug=slug, is_active=True)

    service_id = request.POST.get('service_id')
    staff_id = request.POST.get('staff_id')
    booking_date_str = request.POST.get('date')
    start_time_str = request.POST.get('start_time')
    payment_method = request.POST.get('payment_method', 'online')  # 'online' or 'offline'

    service = get_object_or_404(Service, pk=service_id, business=business, is_active=True)
    staff = None
    if staff_id:
        staff = Staff.objects.filter(pk=staff_id, business=business, is_active=True).first()

    try:
        booking_date = datetime.strptime(booking_date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid date'}, status=400)

    customer_data = {
        'customer_name': request.POST.get('customer_name', '').strip(),
        'customer_email': request.POST.get('customer_email', '').strip(),
        'customer_phone': request.POST.get('customer_phone', '').strip(),
        'customer_notes': request.POST.get('customer_notes', '').strip(),
    }

    if not all([customer_data['customer_name'], customer_data['customer_email'], customer_data['customer_phone']]):
        return JsonResponse({'error': 'Name, email and phone are required.'}, status=400)

    payment_method = request.POST.get('payment_method', 'online')

    booking, error = create_booking_atomic(
        business, service, staff, customer_data, booking_date, start_time_str, payment_method
    )

    if error:
        return JsonResponse({'error': error}, status=409)

    # Send confirmation email (async if Celery available, else sync)
    try:
        from notifications.tasks import task_send_booking_confirmation
        task_send_booking_confirmation.delay(str(booking.pk))
    except Exception:
        try:
            send_booking_confirmation(booking)
        except Exception:
            pass

    return JsonResponse({
        'success': True,
        'booking_id': str(booking.pk),
        'redirect': f'/b/{slug}/confirmation/{booking.pk}/',
    })


def booking_confirmation(request, slug, booking_id):
    """Confirmation page after successful booking."""
    business = get_object_or_404(Business, slug=slug, is_active=True)
    booking = get_object_or_404(Booking, pk=booking_id, business=business)
    css_vars = render_css_vars(business)

    # Generate QR code for check-in
    qr_data = None
    try:
        import qrcode
        import io
        import base64
        qr = qrcode.QRCode(version=1, box_size=6, border=2)
        qr.add_data(f"BOOKIFY:{booking.client_id}:{business.slug}")
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        qr_data = base64.b64encode(buf.getvalue()).decode()
    except Exception:
        pass

    return render(request, 'bookings/confirmation.html', {
        'business': business,
        'booking': booking,
        'css_vars': css_vars,
        'qr_data': qr_data,
    })


def manage_booking(request, slug, booking_id):
    """Allow customer to cancel their booking."""
    business = get_object_or_404(Business, slug=slug, is_active=True)
    booking = get_object_or_404(Booking, pk=booking_id, business=business)

    if request.method == 'POST' and request.POST.get('action') == 'cancel':
        if booking.status not in ('cancelled', 'completed', 'no_show'):
            booking.status = 'cancelled'
            booking.save(update_fields=['status'])
            try:
                from notifications.utils import send_booking_cancellation
                send_booking_cancellation(booking)
            except Exception:
                pass
            return redirect(f'/b/{slug}/confirmation/{booking_id}/?cancelled=1')

    return render(request, 'bookings/manage.html', {
        'business': business,
        'booking': booking,
        'css_vars': render_css_vars(business),
    })
