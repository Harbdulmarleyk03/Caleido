import pytest 
from apps.events.models import EventType
from datetime import timedelta
from django.utils import timezone
from apps.bookings.tests.factories import InviteeFactory, BookingFactory

@pytest.fixture
def event_type(owner):
    return EventType.objects.create(
        owner=owner,
        title="My first event type",
        description="This is my first description",
        duration_minutes=30,
        location_type='zoom',
        buffer_before_min=5,
        buffer_after_min=5,
        min_notice_hours=1,
        max_future_days=1,
        slug="my-first-event-type",
    )

@pytest.fixture
def booking_with_invitee(owner, event_type):
    booking = BookingFactory(
        status='confirmed',
        event_type=event_type,
        start_time=timezone.now() + timedelta(days=2),
        end_time=timezone.now() + timedelta(days=2, hours=1)
    )
    return booking 

@pytest.fixture
def auth_client(api_client, owner): # event type owner
    api_client.force_authenticate(user=owner)
    return api_client
