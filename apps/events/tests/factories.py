from apps.events.models import EventType
from apps.users.tests.factories import UserFactory
import factory

class EventTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EventType

    owner = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f"Event {n}")
    duration_minutes = 30
    location_type = "google_meet"