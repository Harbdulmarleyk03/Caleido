from django.db import models
from common.models import AbstractBaseModel


class StripePayment(AbstractBaseModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
        ("refunded", "Refunded"),
    ]

    payment_intent_id = models.CharField(max_length=255, unique=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES)
    amount_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=3)

    class Meta:
        db_table = "payments_stripe_payment"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.payment_intent_id} — {self.status}"


class StripeRefund(AbstractBaseModel):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("succeeded", "Succeeded"),
        ("failed", "Failed"),
    ]

    payment = models.ForeignKey(StripePayment, on_delete=models.CASCADE, related_name="refunds", db_index=True)
    refund_id = models.CharField(max_length=255, unique=True)
    amount_cents = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    class Meta:
        db_table = "payments_stripe_refund"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.refund_id} — {self.status}"


class ProcessedStripeEvent(models.Model):
    """Idempotency guard — no updated_at needed, append-only."""
    id = models.UUIDField(primary_key=True, default=__import__('uuid').uuid4, editable=False)
    stripe_event_id = models.CharField(max_length=255, unique=True)
    processed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payments_processed_event"

    def __str__(self):
        return self.stripe_event_id