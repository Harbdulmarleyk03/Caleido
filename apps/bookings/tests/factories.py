import factory
from apps.bookings import models
from datetime import timedelta
from apps.events.tests.factories import EventTypeFactory

class InviteeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Invitee 

    name = factory.Faker("name")
    email = factory.Faker("email")
    timezone = factory.Faker("timezone")

class BookingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Booking 

    event_type = factory.SubFactory(EventTypeFactory)
    start_time = factory.Faker("future_datetime", tzinfo=None)
    end_time = factory.LazyAttribute(lambda obj: obj.start_time + timedelta(minutes=30))
    status = "confirmed"
