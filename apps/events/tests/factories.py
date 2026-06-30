from apps.events.models import EventType, AvailabilityRule
from apps.users.tests.factories import UserFactory
import factory
from datetime import timedelta, timezone as dt_timezone


class EventTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EventType

    owner = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Event {n}")
    duration_minutes = 30
    location_type = "google_meet"


class AvailabilityRuleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AvailabilityRule

    event_type = factory.SubFactory(EventTypeFactory)
    day_of_week = 3
    start_time = factory.Faker(
        "future_datetime", end_date="+30d", tzinfo=dt_timezone.utc
    )
    end_time = factory.LazyAttribute(lambda obj: obj.start_time + timedelta(minutes=30))
