from celery import shared_task
from django.core.mail import send_mail
from apps.bookings.tokens import generate_cancel_token
from apps.bookings.models import Booking, BookingAudit
from django.conf import settings
import logging
from zoneinfo import ZoneInfo
from datetime import datetime
from config.celery import app

logger = logging.getLogger(__name__)

def send_invitee_confirmation_email(booking_id, cancel_url):
    booking = Booking.objects.select_related('invitee', 'event_type__owner').get(id=booking_id)
    invitee = booking.invitee
    host = booking.event_type.owner
    invitee_time = booking.start_time.astimezone(ZoneInfo(invitee.timezone))

    send_mail(
        subject="Booking Confirmed",
        message=f"Your booking with {host.name} is confirmed. The event named {booking.event_type.title} will start by {invitee_time}. To cancel your booking, click here: {cancel_url}",
        from_email = settings.DEFAULT_FROM_EMAIL,
        recipient_list = [invitee.email],
    )

def send_host_confirmation_email(booking_id):
    booking = Booking.objects.select_related('invitee', 'event_type__owner').get(id=booking_id)
    host = booking.event_type.owner
    invitee = booking.invitee
    host_time = booking.start_time.astimezone(ZoneInfo(host.timezone))

    send_mail(
        subject="Booking Confirmed",
        message=f"{invitee.name} booked a meeting with you titled {booking.event_type.title} by {host_time}. Be there.",
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
    try:
        booking = Booking.objects.select_related('invitee', 'event_type__owner').get(id=booking_id)
    except Booking.DoesNotExist:
        logger.warning("Booking %s not found when sending cancellation email", booking_id)
        return
     
    if booking.status != 'cancelled':
        return 
    
    invitee = booking.invitee
    host = booking.event_type.owner
    invitee_time = booking.start_time.astimezone(ZoneInfo(invitee.timezone))
    host_time = booking.start_time.astimezone(ZoneInfo(host.timezone))

    try:
        send_mail(
            subject="Booking Cancelled",
            message=f"Your booking with {host.name} titled {booking.event_type.title} by {invitee_time} has been cancelled.",
            from_email = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [invitee.email],
        )
    except Exception as exc:
        self.retry(
            exc=exc,
            countdown=60,
        )
        return 
    
    try:
        send_mail(
            subject="Booking Cancelled",
            #TODO,
            message=f"{invitee.name} has cancelled the meeting with you titled {booking.event_type.title} by {host_time}.",
            from_email = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [host.email],
        )
    except Exception as exc:
        self.retry(
            exc=exc,
            countdown=60,
        )
        
@shared_task(bind=True, max_retries=3)
def send_booking_reschedule(self, booking_id: str):
    try:
        booking = Booking.objects.select_related('invitee', 'event_type__owner').get(id=booking_id)
    except Booking.DoesNotExist:
        logger.warning("Booking %s not found when sending reschedule email", booking_id)
        return
    
    if booking.status != 'confirmed':
        return 
    
    invitee = booking.invitee
    host = booking.event_type.owner
    new_start_time = booking.start_time
    new_end_time = booking.end_time
    invitee_start_time = new_start_time.astimezone(ZoneInfo(invitee.timezone))
    invitee_end_time = new_end_time.astimezone(ZoneInfo(invitee.timezone))
    host_start_time = new_start_time.astimezone(ZoneInfo(host.timezone))
    host_end_time = new_end_time.astimezone(ZoneInfo(host.timezone))

    audit = (BookingAudit.objects.filter(booking=booking, action='rescheduled',).order_by("-changed_at").first())
    if audit:
        old_start = datetime.fromisoformat(audit.previous_data['start_time'])
        old_end = datetime.fromisoformat(audit.previous_data['end_time'])
        old_start_invitee = old_start.astimezone(ZoneInfo(invitee.timezone))
        old_end_invitee = old_end.astimezone(ZoneInfo(invitee.timezone))
        old_start_host = old_start.astimezone(ZoneInfo(host.timezone))
        old_end_host = old_end.astimezone(ZoneInfo(host.timezone))

    else:
        old_start_invitee = old_end_invitee = "unknown"
        old_start_host = old_end_host = "unknown"

    old_24h_task_id = booking.reminder_24h_task_id
    old_1h_task_id = booking.reminder_1h_task_id
    app.control.revoke(old_24h_task_id, terminate=False)
    app.control.revoke(old_1h_task_id, terminate=False)


    token = generate_cancel_token(booking)

    cancel_url = f"{settings.DOMAIN}/cancel?token={token}"

    try:
        send_mail(
            subject="Booking Rescheduled",
            message=f"Your booking with {host.name} is rescheduled. The event named {booking.event_type.title} is longer in the space of {old_start_invitee} to {old_end_invitee} but in the space of {invitee_start_time} to {invitee_end_time}. To cancel your booking, click here: {cancel_url}",
            from_email = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [invitee.email],
        )
    
    except Exception as exc:
        self.retry(
            exc=exc,
            countdown=60,
        )
        return 
    
    try:
        send_mail(
            subject="Booking Rescheduled",
            #TODO,
            message=f"{invitee.name} has rescheduled the meeting with you titled {booking.event_type.title} that started initially from {old_start_host} to {old_end_host}. It has been rescheduled from {host_start_time} to {host_end_time} now.",
            from_email = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [host.email],
        )
    except Exception as exc:
        self.retry(
            exc=exc,
            countdown=60,
        )

@shared_task(bind=True, max_retries=3)
def send_booking_reminder(self, booking_id: str, reminder_type: str):
    try:
        booking = Booking.objects.select_related('invitee', 'event_type__owner').get(id=booking_id)
    except Booking.DoesNotExist:
        logger.warning("Booking %s not found when sending reminder email", booking_id)
        return
    
    if booking.status != "confirmed":
        return 
    
    invitee = booking.invitee
    host = booking.event_type.owner

    try:
        send_mail(
            subject="Booking Reminder",
            message=f"Your booking with {host.name} titled {booking.event_type.title} is in {reminder_type}. Get ready.",
            from_email = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [invitee.email],
        )
    
    except Exception as exc:
        self.retry(
            exc=exc,
            countdown=60,
        )
        return 
    try:
        send_mail(
            subject="Booking Reminder",
            #TODO,
            message=f"Your booking with {invitee.name} titled {booking.event_type.title} is in {reminder_type}. Get ready.",
            from_email = settings.DEFAULT_FROM_EMAIL,
            recipient_list = [host.email],
        )
    except Exception as exc:
        self.retry(
            exc=exc,
            countdown=60,
        )
