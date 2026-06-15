from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def _send(subject, text_body, html_body, to_email):
    try:
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.EMAIL_HOST_USER,
            to=[to_email],
        )
        msg.attach_alternative(html_body, 'text/html')
        msg.send()
    except Exception as e:
        logger.error(f"Email send failed to {to_email}: {e}")


def send_booking_confirmation(booking):
    subject = f'Booking Confirmed — {booking.business.name}'
    ctx = {'booking': booking}
    html = render_to_string('notifications/email/confirmation.html', ctx)
    text = render_to_string('notifications/email/confirmation.txt', ctx)
    _send(subject, text, html, booking.customer_email)


def send_booking_reminder(booking):
    subject = f'Reminder: Your appointment at {booking.business.name}'
    ctx = {'booking': booking}
    html = render_to_string('notifications/email/reminder.html', ctx)
    text = render_to_string('notifications/email/reminder.txt', ctx)
    _send(subject, text, html, booking.customer_email)


def send_booking_cancellation(booking):
    subject = f'Booking Cancelled — {booking.business.name}'
    ctx = {'booking': booking}
    html = render_to_string('notifications/email/cancellation.html', ctx)
    text = render_to_string('notifications/email/cancellation.txt', ctx)
    _send(subject, text, html, booking.customer_email)


def send_rebook_magic_link(booking, rebook_url):
    subject = f'We miss you! Rebook at {booking.business.name}'
    ctx = {'booking': booking, 'rebook_url': rebook_url}
    html = render_to_string('notifications/email/rebook.html', ctx)
    text = render_to_string('notifications/email/rebook.txt', ctx)
    _send(subject, text, html, booking.customer_email)
