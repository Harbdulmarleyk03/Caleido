from apps.bookings.models import Booking, Invitee, BookingAudit
from django.db import transaction
from common.exceptions import ConflictError

class BookingService:

    @staticmethod
    def create_booking(start_time, end_time, event_type, invitee_name, invitee_email, invitee_timezone, invitee_notes, idempotency_key, user):
        existing = Booking.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
                return existing
        with transaction.atomic():
            conflicting_booking = Booking.objects.select_for_update().filter(event_type=event_type, status='confirmed', start_time__lt=end_time, end_time__gt=start_time)
            if conflicting_booking.exists():
                 raise ConflictError("The slot is already taken.")
            booking = Booking.objects.create(start_time=start_time, end_time=end_time, idempotency_key=idempotency_key, status='confirmed', event_type=event_type)
            Invitee.objects.create(
                booking=booking, name=invitee_name, email=invitee_email, timezone=invitee_timezone, notes=invitee_notes)
            BookingAudit.objects.create(action="created", previous_data={}, changed_by=user, booking=booking)
            return booking

