import pytest
from apps.users.tests.factories import UserFactory
from apps.events.models import EventType, AvailabilityRule
from django.urls import reverse
from datetime import time, date, datetime  
import pytz 
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
        min_notice_hours=4,
        max_future_days=60,
        slug="my-first-event-type",
    )

@pytest.fixture
def availability_rule(event_type):
    return AvailabilityRule.objects.create(
            event_type=event_type,
            day_of_week=3,
            start_time="9:00:00",
            end_time="12:00:00"
    )

@pytest.fixture
def auth_client(api_client, owner):
    api_client.force_authenticate(user=owner)
    return api_client

@pytest.mark.django_db
class TestSlotListView:

    def test_missing_date(self, auth_client, event_type):
        url = reverse('event-type-slots', kwargs={'event_type_id': event_type.id})
        data = {"timezone": 'UTC'}
        response = auth_client.get(url, data)
        assert response.status_code == 400 

    def test_invalid_date_format(self, auth_client, event_type):
        url = reverse('event-type-slots', kwargs={'event_type_id': event_type.id})
        data = {'date': "Not/Valid", 'timezone': 'UTC'}
        response = auth_client.get(url, data)
        assert response.status_code == 400 

    def test_invalid_timezone_format(self, auth_client, event_type):
        url = reverse('event-type-slots', kwargs={'event_type_id': event_type.id})
        data = {'date': '2026-05-14', 'timezone': "Not/Valid"}
        response = auth_client.get(url, data)
        assert response.status_code == 400 

    def test_inactive_event_type(self, auth_client, event_type):
        inactive = EventType.objects.create(
            owner=event_type.owner, title="Inactive", slug="inactive-event",
            duration_minutes=30, location_type='zoom', is_active=False,
        )
        url = reverse('event-type-slots', kwargs={'event_type_id': inactive.id})
        response = auth_client.get(url, {'date': '2026-05-14', 'timezone': 'UTC'})
        assert response.status_code == 404
        
    def test_valid_requests_with_no_rules(self, auth_client, event_type):
        url = reverse('event-type-slots', kwargs={'event_type_id': event_type.id})

        response = auth_client.get(url, {'date': '2026-05-14', 'timezone': 'Africa/Lagos'})
        assert response.status_code == 200 
        assert response.data == {'slots': []}

    def test_valid_requests_with_rules(self, auth_client, event_type):
        url = reverse('event-type-slots', kwargs={'event_type_id': event_type.id})
        AvailabilityRule.objects.create(
            event_type=event_type,
            day_of_week=3,
            start_time="9:00:00",
            end_time="12:00:00"
        )
        response = auth_client.get(url, {'date': '2026-05-21', 'timezone': 'Africa/Lagos'})
        assert response.status_code == 200 
        assert len(response.data['slots']) > 0
            
    def test_existing_booking_blocks_slot(self, auth_client, event_type):
        target = date(2026, 5, 14)
        AvailabilityRule.objects.create(
            event_type=event_type,
            day_of_week=3,
            start_time=time(9, 0),
            end_time=time(10, 0),
        )
        tz = pytz.timezone('Africa/Lagos')
        start_time = tz.localize(datetime.combine(target, time(9, 0)))
        end_time = tz.localize(datetime.combine(target, time(9, 30)))
        Booking.objects.create(
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            status='confirmed', 
            assigned_to=None,
            idempotency_key='test-booking-1',
        )
        url = reverse('event-type-slots', kwargs={'event_type_id': event_type.id})
        response = auth_client.get(url, {'date': '2026-05-14', 'timezone': 'Africa/Lagos'})
        assert response.status_code == 200
        slots = response.data["slots"]
        assert start_time.isoformat() not in [slot["start"] for slot in slots]