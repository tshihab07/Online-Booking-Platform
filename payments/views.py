import json
import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import logging

logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(request, booking_id):
    """Create a Stripe Checkout session for a booking."""
    from bookings.models import Booking
    booking = get_object_or_404(Booking, pk=booking_id)
    business = booking.business

    base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
    slug = business.slug

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': business.currency.lower(),
                    'product_data': {
                        'name': booking.service.name,
                        'description': f"Appointment on {booking.date} at {booking.start_time}",
                    },
                    'unit_amount': int(booking.amount * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{base_url}/b/{slug}/confirmation/{booking_id}/?payment=success",
            cancel_url=f"{base_url}/b/{slug}/confirmation/{booking_id}/?payment=cancelled",
            metadata={
                'booking_id': str(booking_id),
                'business_slug': slug,
            },
        )
        return JsonResponse({'session_id': session.id, 'url': session.url})
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Handle Stripe webhook events."""
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        logger.error(f"Webhook error: {e}")
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        booking_id = session['metadata'].get('booking_id')
        if booking_id:
            try:
                from bookings.models import Booking
                booking = Booking.objects.get(pk=booking_id)
                booking.payment_status = 'paid'
                booking.payment_id = session.get('payment_intent', '')
                booking.status = 'confirmed'
                booking.save(update_fields=['payment_status', 'payment_id', 'status'])
                logger.info(f"Payment confirmed for booking {booking_id}")
            except Exception as e:
                logger.error(f"Webhook booking update failed: {e}")

    return HttpResponse(status=200)
