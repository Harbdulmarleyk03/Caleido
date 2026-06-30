import factory
from apps.bookings import models
from datetime import timedelta, timezone as dt_timezone
from apps.events.tests.factories import EventTypeFactory


class BookingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Booking
        skip_postgeneration_save = True

    event_type = factory.SubFactory(EventTypeFactory)
    start_time = factory.Faker(
        "future_datetime", end_date="+30d", tzinfo=dt_timezone.utc
    )
    end_time = factory.LazyAttribute(lambda obj: obj.start_time + timedelta(minutes=30))
    idempotency_key = factory.Faker("uuid4")
    status = "confirmed"
    invitee = factory.RelatedFactory(
        "apps.bookings.tests.factories.InviteeFactory",
        factory_related_name="booking",
    )


class InviteeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Invitee

    booking = factory.SubFactory(BookingFactory, invitee=None)
    name = factory.Faker("name")
    email = factory.Faker("email")
    timezone = factory.Faker("timezone")
