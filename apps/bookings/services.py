from apps.bookings.models import Booking, Invitee, BookingAudit
from django.db import IntegrityError, transaction
from common.exceptions import ConflictError

class BookingService:

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
            booking.save()
            audit_user = (
                user
                if user and user.is_authenticated
                else booking.event_type.owner
            )
            BookingAudit.objects.create(action="cancelled", previous_data=previous, changed_by=audit_user, booking=booking)
    
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
    