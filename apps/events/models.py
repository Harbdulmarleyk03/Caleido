from django.db import IntegrityError, models, transaction
from common.models import AbstractBaseModel
from apps.users.models import User
from apps.events.services.slug_services import SlugService

class EventType(AbstractBaseModel):
    LOCATION_CHOICES = [
        ("google_meet", "Google Meet"),
        ("zoom", "Zoom"),
        ("phone", "Phone"),
        ("in_person", "In Person"),
        ("custom", "Custom"),
    ]
    ASSIGNMENT_CHOICES = [
        ("direct", "Direct"),
        ("round_robin", "Round Robin"),
        ("collective", "Collective"),
    ]

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="event_types", db_index=True)
    team = models.ForeignKey("teams.Team", on_delete=models.CASCADE, related_name="event_types", null=True, blank=True, db_index=True)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=100)
    description = models.TextField(blank=True, null=True)
    duration_minutes = models.PositiveIntegerField()
    color = models.CharField(max_length=7, default="#0069FF")
    location_type = models.CharField(max_length=30, choices=LOCATION_CHOICES)
    location_value = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_paid = models.BooleanField(default=False)
    price_cents = models.PositiveIntegerField(null=True, blank=True)
    currency = models.CharField(max_length=3, null=True, blank=True, default="USD")
    assignment_rule = models.CharField(max_length=20, choices=ASSIGNMENT_CHOICES, default="direct",)
    buffer_before_min = models.PositiveIntegerField(default=0)
    buffer_after_min = models.PositiveIntegerField(default=0)
    min_notice_hours = models.PositiveIntegerField(default=24)
    max_future_days = models.PositiveIntegerField(default=60)

    class Meta:
        db_table = "events_event_type"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["owner", "slug"],
                name="unique_owner_slug")]

    def __str__(self):
        return f"{self.title} ({self.owner.email})"

    def save(self, *args, **kwargs):
        if not self.slug:  # only generate if empty
            self.slug = SlugService.generate_unique_slug(EventType, self.title)
        try:
            with transaction.atomic():
                super().save(*args, **kwargs)
        except IntegrityError:
        # regenerate and retry once
            with transaction.atomic():
                self.slug = SlugService.generate_unique_slug(EventType, self.title)
                super().save(*args, **kwargs)

class AvailabilityRule(AbstractBaseModel):
    event_type = models.ForeignKey(EventType, on_delete=models.CASCADE, related_name="availability_rules", db_index=True)
    day_of_week = models.SmallIntegerField()  # 0=Monday, 6=Sunday
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        db_table = "events_availability_rule"
        ordering = ["day_of_week", "start_time"]

    def __str__(self):
        return f"{self.event_type.title} — day {self.day_of_week} {self.start_time}–{self.end_time}"

class DateOverride(AbstractBaseModel):
    event_type = models.ForeignKey(EventType, on_delete=models.CASCADE, related_name="date_overrides", db_index=True)
    specific_date = models.DateField()
    is_unavailable = models.BooleanField(default=False)
    custom_start = models.TimeField(null=True, blank=True)
    custom_end = models.TimeField(null=True, blank=True)

    class Meta:
        db_table = "events_date_override"
        constraints = [
            models.UniqueConstraint(
                fields=["event_type", "specific_date"],
                name="unique_event_type_date")]

    def __str__(self):
        return f"{self.event_type.title} — {self.specific_date}"


class EventTypeQuestion(AbstractBaseModel):
    QUESTION_TYPES = [
        ("text", "Text"),
        ("select", "Select"),
        ("checkbox", "Checkbox"),
    ]

    event_type = models.ForeignKey(EventType, on_delete=models.CASCADE, related_name="questions", db_index=True)
    question_text = models.CharField(max_length=500)
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES)
    options = models.JSONField(null=True, blank=True)  # for select/checkbox
    is_required = models.BooleanField(default=False)
    display_order = models.SmallIntegerField(default=0)

    class Meta:
        db_table = "events_question"
        ordering = ["display_order"]

    def __str__(self):
        return f"{self.event_type.title} — {self.question_text[:50]}"