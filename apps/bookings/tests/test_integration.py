import pytest
from apps.events.models import EventType
from apps.users.tests.factories import UserFactory
from django.urls import reverse 
from apps.bookings.services import BookingService
from django.utils import timezone
from datetime import timedelta
from apps.bookings.models import BookingAudit

@pytest.fixture
def other_user(db):
    return UserFactory(is_verified=True)

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
        slug="my-first-event-type")

@pytest.fixture
def owner(db):
    return UserFactory(is_verified=True)

@pytest.fixture
def auth_client(api_client, owner):
    api_client.force_authenticate(user=owner)
    return api_client

start = timezone.now() + timedelta(days=1)
end = start + timedelta(minutes=30)

@pytest.mark.django_db
class TestBookingIntegration:

    def test_cancel_confirmed_booking(self, auth_client, owner, event_type):
        url = reverse('booking-cancel', args=[booking.id])
        booking, _ = BookingService.create_booking(
            start_time=start,
            end_time=end,
            event_type=event_type,
            invitee_name='Lanre',
            invitee_email='lanre@example.com',
            invitee_timezone='America/New_York',
            idempotency_key='unique-key-001',
            invitee_notes=None,
            user=owner
        )
        response = auth_client.patch(url, format='json')
        assert response.status_code == 200
        booking.refresh_from_db()
        assert booking.status == "cancelled" 
        audit = BookingAudit.objects.filter(booking=booking, action='cancelled').first()
        assert audit is not None
        assert audit.previous_data['status'] == 'confirmed'



    def test_cancel_already_cancelled_booking(self, auth_client, event_type):
        url = reverse('booking-list')