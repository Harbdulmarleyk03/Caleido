from apps.bookings.models import Booking, Invitee, BookingAudit
from django.db import IntegrityError, transaction
from common.exceptions import ConflictError
from apps.bookings.tasks import send_booking_confirmation_email, send_booking_cancellation_email, send_booking_reschedule_email, send_booking_reminder_email
from config.celery import app 
from datetime import timedelta
from django.utils import timezone


class BookingService:

    @staticmethod
    def schedule_booking_reminder(booking_id):
        booking = Booking.objects.select_related('invitee', 'event_type__owner').get(id=booking_id)

        reminder_24h_eta = booking.start_time - timedelta(hours=24)
        reminder_1h_eta = booking.start_time - timedelta(hours=1)
        result_24h = None
        result_1h = None

        if reminder_24h_eta > timezone.now():
            result_24h = send_booking_reminder_email.apply_async(
                args=[str(booking.id), "24h"],
                eta=reminder_24h_eta,
            )

        if reminder_1h_eta > timezone.now():
            result_1h = send_booking_reminder_email.apply_async(
                args=[str(booking.id), "1h"],
                eta=reminder_1h_eta,
            )

        booking.reminder_24h_task_id = result_24h.id if result_24h else None 
        booking.reminder_1h_task_id = result_1h.id if result_1h else None 

        booking.save(
        update_fields=[
            "reminder_24h_task_id",
            "reminder_1h_task_id",
        ]
    )

    @staticmethod
    def create_booking(start_time, end_time, event_type, invitee_name, invitee_email, invitee_timezone, invitee_notes, idempotency_key, user):
        existing = Booking.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing, False
        with transaction.atomic():
            conflicting_booking = Booking.objects.select_for_update().filter(event_type=event_type, status='confirmed', start_time__lt=end_time, end_time__gt=start_time)
            if conflicting_booking.exists():
                 raise ConflictError("The slot is already taken.")
            try:
                booking = Booking.objects.create(start_time=start_time, end_time=end_time, idempotency_key=idempotency_key, status='confirmed', event_type=event_type)
            except IntegrityError:  
                existing = Booking.objects.filter(idempotency_key=idempotency_key).first()
                if existing:
                    return existing, False  
                raise 
            Invitee.objects.create(
                booking=booking, name=invitee_name, email=invitee_email, timezone=invitee_timezone, notes=invitee_notes)
            audit_user = (
                user
                if user and user.is_authenticated
                else booking.event_type.owner
            )
            BookingAudit.objects.create(action="created", previous_data={}, changed_by=audit_user, booking=booking)
            transaction.on_commit(lambda: send_booking_confirmation_email.delay(str(booking.id)))
            transaction.on_commit(lambda: BookingService.schedule_booking_reminder(str(booking.id)))
            return booking, True

    @staticmethod
    def cancel_booking(booking, user):
        with transaction.atomic():
            if booking.status == "cancelled":
                raise ConflictError("Booking already cancelled.")
            previous = {
                'status': booking.status,
                'start_time': booking.start_time.isoformat(),
                'end_time': booking.end_time.isoformat(),
            }
            booking.status = "cancelled"
            task_id_24h = booking.reminder_24h_task_id
            task_id_1h = booking.reminder_1h_task_id
            booking.reminder_24h_task_id = None
            booking.reminder_1h_task_id = None
            booking.save()
            audit_user = (
                user
                if user and user.is_authenticated
                else booking.event_type.owner
            )
            BookingAudit.objects.create(action="cancelled", previous_data=previous, changed_by=audit_user, booking=booking)
            transaction.on_commit(lambda: app.control.revoke(task_id_24h, terminate=False) if task_id_24h else None)
            transaction.on_commit(lambda: app.control.revoke(task_id_1h, terminate=False) if task_id_1h else None)
            transaction.on_commit(lambda: send_booking_cancellation_email.delay(str(booking.id)))
       
    @staticmethod
    def reschedule_booking(booking, user, start_time, end_time):
        with transaction.atomic():
            booking = Booking.objects.select_for_update().get(id=booking.id)
            if booking.status == "cancelled":
                raise ConflictError("Cannot reschedule a cancelled booking.")
            conflict = Booking.objects.select_for_update().filter(event_type=booking.event_type, status='confirmed', start_time__lt=end_time, end_time__gt=start_time).exclude(id=booking.id)
            if conflict.exists():
                raise ConflictError("The new slot is already taken.")
            previous = {
                'status': booking.status,
                'start_time': booking.start_time.isoformat(),
                'end_time': booking.end_time.isoformat(),
            }
            booking.start_time = start_time
            booking.end_time = end_time
            booking.status = "confirmed"
            booking.save()
            audit_user = (
                user
                if user and user.is_authenticated
                else booking.event_type.owner
            )
            BookingAudit.objects.create(action="rescheduled", previous_data=previous, changed_by=audit_user, booking=booking)
            old_24h_task_id = booking.reminder_24h_task_id
            old_1h_task_id = booking.reminder_1h_task_id
            transaction.on_commit(lambda: app.control.revoke(old_24h_task_id, terminate=False) if old_24h_task_id else None)
            transaction.on_commit(lambda: app.control.revoke(old_1h_task_id, terminate=False) if old_1h_task_id else None)
            transaction.on_commit(lambda: BookingService.schedule_booking_reminder(str(booking.id)))
            transaction.on_commit(lambda: send_booking_reschedule_email.delay(str(booking.id)))

          