import pytest
from apps.events.models import EventType
from apps.users.tests.factories import UserFactory
from django.urls import reverse 
from apps.bookings.services import BookingService
from django.utils import timezone
from datetime import timedelta
from apps.bookings.models import BookingAudit
from apps.bookings.tokens import generate_cancel_token, generate_reschedule_token


@pytest.fixture
def other_user(db):
    return UserFactory(is_verified=True)

@pytest.fixture
def other_event_type(other_user):
    return EventType.objects.create(
        owner=other_user,
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

    def test_owner_cancel_confirmed_booking(self, auth_client, owner, event_type):
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
        url = reverse('booking-cancel', args=[booking.id])
        response = auth_client.patch(url, format='json')
        assert response.status_code == 200
        booking.refresh_from_db()
        assert booking.status == "cancelled" 
        audit = BookingAudit.objects.filter(booking=booking, action='cancelled').first()
        assert audit is not None
        assert audit.previous_data['status'] == 'confirmed'


    def test_owner_cancel_already_cancelled_booking(self, auth_client, owner, event_type):
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
        url = reverse('booking-cancel', args=[booking.id])
        response = auth_client.patch(url, format='json')
        assert response.status_code == 200
        booking.refresh_from_db()
        assert booking.status == "cancelled"
        audit = BookingAudit.objects.filter(booking=booking, action='cancelled').first()
        assert audit is not None
        assert audit.previous_data['status'] == 'confirmed'

        url = reverse('booking-cancel', args=[booking.id])
        response = auth_client.patch(url, format='json')
        assert response.status_code == 409


    def test_non_owner_cannot_cancel_booking(self, auth_client, other_user, other_event_type):
        booking, _ = BookingService.create_booking(
            start_time=start,
            end_time=end,
            event_type=other_event_type,
            invitee_name='Lanre',
            invitee_email='lanre@example.com',
            invitee_timezone='America/New_York',
            idempotency_key='unique-key-001',
            invitee_notes=None,
            user=other_user
        )
        url = reverse('booking-cancel', args=[booking.id])
        response = auth_client.patch(url, format='json')
        assert response.status_code == 403

    def test_unauthenticated_user_with_no_token(self, auth_client, owner, event_type):
        auth_client.force_authenticate(user=None)
        booking, _ = BookingService.create_booking(
            start_time=start,
            end_time=end,
            event_type=event_type,
            invitee_name='Lanre',
            invitee_email='lanre@example.com',
            invitee_timezone='America/New_York',
            idempotency_key='unique-key-001',
            invitee_notes=None,
            user=owner,
        )
        url = reverse('booking-cancel', args=[booking.id])
        response = auth_client.patch(url, format='json')
        assert response.status_code == 401

    def test_invitee_cancels_with_valid_token(self, api_client, other_user, other_event_type):
        booking, _ = BookingService.create_booking(
            start_time=start,
            end_time=end,
            event_type=other_event_type,
            invitee_name='Lanre',
            invitee_email='lanre@example.com',
            invitee_timezone='America/New_York',
            idempotency_key='unique-key-001',
            invitee_notes=None,
            user=other_user,
        )
        token = generate_cancel_token(booking)
        url = reverse('booking-cancel', args=[booking.id])
        response = api_client.patch(url, {'token': str(token)}, format='json')
        booking.refresh_from_db()
        assert response.status_code == 200
        assert booking.status == "cancelled"

    def test_invitee_cancels_with_expired_token(self, api_client, other_user, other_event_type):
        booking, _ = BookingService.create_booking(
            start_time=start,
            end_time=end,
            event_type=other_event_type,
            invitee_name='Lanre',
            invitee_email='lanre@example.com',
            invitee_timezone='America/New_York',
            idempotency_key='unique-key-001',
            invitee_notes=None,
            user=other_user,
        )
        token = "not.valid.token"
        url = reverse('booking-cancel', args=[booking.id])
        response = api_client.patch(url, {'token': str(token)}, format='json')
        assert response.status_code == 401


    def test_invitee_uses_token_for_wrong_booking(self, api_client, other_user, event_type):
        booking, _ = BookingService.create_booking(
            start_time=start,
            end_time=end,
            event_type=event_type,
            invitee_name='Lanre',
            invitee_email='lanre@example.com',
            invitee_timezone='America/New_York',
            idempotency_key='unique-key-001',
            invitee_notes=None,
            user=other_user,
        )        

        token_1 = generate_cancel_token(booking)
        booking, _ = BookingService.create_booking(
            start_time=start + timedelta(hours=2),
            end_time=end + timedelta(hours=2),
            event_type=event_type,
            invitee_name='Lanre',
            invitee_email='lanre@example.com',
            invitee_timezone='America/New_York',
            idempotency_key='unique-key-002',
            invitee_notes=None,
            user=other_user,
        )        
        token_2 = generate_cancel_token(booking)
        url = reverse('booking-cancel', args=[booking.id])
        response = api_client.patch(url, {'token': str(token_1)}, format='json')
        assert response.status_code == 401