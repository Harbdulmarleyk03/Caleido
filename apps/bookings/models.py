from django.db import models
from common.models import AbstractBaseModel
from apps.users.models import User

class Booking(AbstractBaseModel):
    STATUS_CHOICES = [
        ("confirmed", "Confirmed"),
        ("cancelled", "Cancelled"),
        ("rescheduled", "Rescheduled"),
    ]

    event_type = models.ForeignKey("events.EventType", on_delete=models.PROTECT, related_name="bookings", db_index=True)
    assigned_to = models.ForeignKey(User, on_delete=models.PROTECT, related_name="assigned_bookings", null=True, blank=True, db_index=True)
    start_time = models.DateTimeField()   # always UTC
    end_time = models.DateTimeField()     # always UTC
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="confirmed")
    idempotency_key = models.CharField(max_length=255, unique=True)
    cancel_reason = models.TextField(blank=True, null=True)
    google_event_id = models.CharField(max_length=255, blank=True, null=True)
    google_meet_link = models.TextField(blank=True, null=True)
    stripe_payment = models.ForeignKey("payments.StripePayment", on_delete=models.SET_NULL, null=True, blank=True, related_name="bookings")

    class Meta:
        db_table = "bookings_booking"
        ordering = ["start_time"]
        indexes = [
            models.Index(
                fields=["event_type", "start_time", "status"],
                name="idx_booking_conflict_check")]

    def __str__(self):
        return f"Booking {self.id} — {self.status}"


class Invitee(AbstractBaseModel):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="invitee")
    name = models.CharField(max_length=200)
    email = models.EmailField()
    timezone = models.CharField(max_length=50)
    locale = models.CharField(max_length=10, default="en")
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "bookings_invitee"

    def __str__(self):
        return f"{self.name} <{self.email}>"


class BookingAnswer(AbstractBaseModel):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="answers", db_index=True)
    question = models.ForeignKey("events.EventTypeQuestion", on_delete=models.CASCADE, related_name="answers", db_index=True)
    answer_text = models.TextField()

    class Meta:
        db_table = "bookings_answer"
        constraints = [
            models.UniqueConstraint(
                fields=["booking", "question"],
                name="unique_booking_question")]

    def __str__(self):
        return f"Answer to {self.question.question_text[:30]}"


class BookingAudit(models.Model):
    ACTION_CHOICES = [
        ("created", "Created"),
        ("cancelled", "Cancelled"),
        ("rescheduled", "Rescheduled"),
    ]

    id = models.UUIDField(primary_key=True, default=__import__('uuid').uuid4, editable=False)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="audit_logs", db_index=True)
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    previous_data = models.JSONField(null=True, blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "bookings_audit"
        ordering = ["changed_at"]

    def __str__(self):
        return f"{self.action} — {self.booking_id} at {self.changed_at}"