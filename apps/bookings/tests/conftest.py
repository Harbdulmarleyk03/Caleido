import pytest 
from apps.users.tests.factories import UserFactory
from apps.events.models import EventType
from apps.bookings.models import Booking


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
def invitee(db): # invitee 
    return UserFactory(is_verified=True)

@pytest.fixture
def booking(invitee, event_type):
    return Booking.objects.create(
        event_type=event_type,
        assigned_to=invitee,
        start_time='',
        end_time='',
        status='confirmed',
        idempotency_key='',
        reminder_24h_task_id='',
        reminder_1h_task_id=''
    )

@pytest.fixture
def auth_client(api_client, owner): # event type owner
    api_client.force_authenticate(user=owner)
    return api_client
