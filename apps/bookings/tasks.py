from celery import shared_task
from django.core.mail import send_mail
from apps.bookings.tokens import generate_cancel_token
from apps.bookings.models import Booking
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_invitee_confirmation_email(booking_id, cancel_url):
    booking = Booking.objects.select_related('invitee', 'event_type__owner').get(id=booking_id)
    invitee = booking.invitee
    host = booking.event_type.owner

    send_mail(
        subject="Booking Confirmed",
        message=f"Your booking with {host.name} is confirmed. The event named {booking.event_type.title} will start by {booking.start_time}. To cancel your booking, click here: {cancel_url}",
        from_email = settings.DEFAULT_FROM_EMAIL,
        recipient_list = [invitee.email],
    )

def send_host_confirmation_email(booking_id):
    booking = Booking.objects.select_related('invitee', 'event_type__owner').get(id=booking_id)
    host = booking.event_type.owner
    invitee = booking.invitee

    send_mail(
        subject="Booking Confirmed",
        message=f"{invitee.name} booked a meeting with you titled {booking.event_type.title} by {booking.start_time}. Be there.",
        from_email = settings.DEFAULT_FROM_EMAIL,
        recipient_list = [host.email],
    )
    
@shared_task(bind=True, max_retries=3)
def send_booking_confirmation(self, booking_id: str):
    try:
        booking = Booking.objects.select_related('invitee', 'event_type__owner').get(id=booking_id)
    except Booking.DoesNotExist:
        logger.warning("Booking %s not found when sending confirmation email", booking_id)
        return 
    
    if booking.status != 'confirmed':
        return 

    token = generate_cancel_token(booking)
    cancel_url = f"{settings.DOMAIN}/cancel?token={token}"

    try:
        send_invitee_confirmation_email(booking_id, cancel_url) 
    except Exception as exc:
        self.retry(
            exc=exc,
            countdown=60,
        )
        return 
    try:
        send_host_confirmation_email(booking_id) 
    except Exception as exc:
        self.retry(
            exc=exc,
            countdown=60,
        )
        
@shared_task(bind=True, max_retries=3)
def send_booking_cancellation(self, booking_id: str):
    pass 