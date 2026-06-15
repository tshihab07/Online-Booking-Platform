from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def task_send_booking_confirmation(self, booking_id):
    try:
        from bookings.models import Booking
        from .utils import send_booking_confirmation
        booking = Booking.objects.get(pk=booking_id)
        send_booking_confirmation(booking)
    except Exception as exc:
        logger.error(f"Confirmation task failed for {booking_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def task_send_booking_reminder(self, booking_id):
    try:
        from bookings.models import Booking
        from .utils import send_booking_reminder
        booking = Booking.objects.get(pk=booking_id)
        send_booking_reminder(booking)
    except Exception as exc:
        logger.error(f"Reminder task failed for {booking_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def task_send_booking_cancellation(self, booking_id):
    try:
        from bookings.models import Booking
        from .utils import send_booking_cancellation
        booking = Booking.objects.get(pk=booking_id)
        send_booking_cancellation(booking)
    except Exception as exc:
        logger.error(f"Cancellation task failed for {booking_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)
