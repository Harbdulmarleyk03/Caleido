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
        generate_cancel_token(booking)
        url = reverse('booking-cancel', args=[booking.id])
        response = api_client.patch(url, {'token': str(token_1)}, format='json')
        assert response.status_code == 401

    def test_owner_reschedules_a_free_slot(self, auth_client, owner, event_type):
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
        data = {
            "start_time": start + timedelta(hours=2)
        }
        url = reverse('booking-reschedule', args=[booking.id])
        response = auth_client.patch(url, data, format='json')
        assert response.status_code == 200 
        booking.refresh_from_db()
        assert booking.start_time == start + timedelta(hours=2)
        assert booking.status == "confirmed"
        audit = BookingAudit.objects.filter(booking=booking, action='rescheduled').first()
        assert audit is not None
        assert audit.previous_data['status'] == 'confirmed'              

    def test_owner_reschedules_to_a_taken_slot(self, auth_client, owner, event_type):  
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
        booking2, _ = BookingService.create_booking(
            start_time=start + timedelta(hours=2),
            end_time=end + timedelta(hours=2),
            event_type=event_type,
            invitee_name='Lanre',
            invitee_email='lanre@example.com',
            invitee_timezone='America/New_York',
            idempotency_key='unique-key-002',
            invitee_notes=None,
            user=owner,
        )  
        data = {
            "start_time": start + timedelta(hours=2)
        }
        url = reverse('booking-reschedule', args=[booking.id])
        response = auth_client.patch(url, data, format='json')
        assert response.status_code == 409

    def test_owner_reschedules_a_cancelled_booking(self, auth_client, owner, event_type):
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
        BookingService.cancel_booking(booking=booking, user=owner)
    
        data = {'start_time': start + timedelta(minutes=30)}
        url = reverse('booking-reschedule', args=[booking.id])
        response = auth_client.patch(url, data, format='json')
        assert response.status_code == 409

    def test_new_slot_in_the_past(self, auth_client, owner, event_type):
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
        data = {'start_time': timezone.now() - timedelta(hours=1)}
        url = reverse('booking-reschedule', args=[booking.id])
        response = auth_client.patch(url, data, format='json')
        assert response.status_code == 400

    def test_invitee_reschedules_with_valid_token(self, api_client, other_user, other_event_type):
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
        token = generate_reschedule_token(booking)
        url = reverse('booking-reschedule', args=[booking.id])
        response = api_client.patch(url, {'token': str(token), 'start_time': (start + timedelta(hours=2)).isoformat()}, format='json')        
        booking.refresh_from_db()
        assert response.status_code == 200
        assert booking.status == "confirmed"
        assert booking.start_time == start + timedelta(hours=2)
    
    def test_same_slot_as_current_booking(self, api_client, other_user, other_event_type):
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
        token = generate_reschedule_token(booking)
        url = reverse('booking-reschedule', args=[booking.id])
        response = api_client.patch(url, {'token': str(token), 'start_time': start.isoformat()}, format='json')        
        booking.refresh_from_db()
        assert response.status_code == 200

    def test_only_bookings_for_the_authenticated_user_event_types(self, auth_client, owner, event_type):
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
        url = reverse('booking-list')
        response = auth_client.get(url, format='json')
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == str(booking.id)

    def test_filter_by_status(self, auth_client, owner, event_type):
        booking_confirmed, _ = BookingService.create_booking(
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
        booking_cancelled, _ = BookingService.create_booking(
            start_time=start + timedelta(hours=2),
            end_time=end + timedelta(hours=2),
            event_type=event_type,
            invitee_name='Lanre',
            invitee_email='lanre@example.com',
            invitee_timezone='America/New_York',
            idempotency_key='unique-key-002',
            invitee_notes=None,
            user=owner,
        )  
        BookingService.cancel_booking(booking=booking_cancelled, user=owner)
        data = {'status': 'confirmed'}
        url = reverse('booking-list')
        response = auth_client.get(url, data, format='json')
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == str(booking_confirmed.id)
        assert response.data['results'][0]['status'] == "confirmed"

    def test_filter_by_event_type_id(self, auth_client, owner, event_type):
        other_event_type = EventType.objects.create(
            owner=owner,
            title="My second event type",
            description="This is my second description",
            duration_minutes=60,
            location_type='zoom',
            buffer_before_min=5,
            buffer_after_min=5,
            min_notice_hours=1,
            max_future_days=1,
            slug="my-second-event-type",
        )
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
        booking_2, _ = BookingService.create_booking(
            start_time=start,
            end_time=end,
            event_type=other_event_type,
            invitee_name='Lanre',
            invitee_email='lanre@example.com',
            invitee_timezone='America/New_York',
            idempotency_key='unique-key-002',
            invitee_notes=None,
            user=owner,
        )
        url = reverse('booking-list')
        response = auth_client.get(url, {'event_type_id': event_type.id}, format='json')
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == str(booking.id)

    def test_filter_by_start_time_range(self, auth_client, owner, event_type):
        start_time_after = start + timedelta(minutes=30)
        start_time_before = start + timedelta(hours=4)
        booking_1, _ = BookingService.create_booking(
            start_time=start_time_after,
            end_time=end,
            event_type=event_type,
            invitee_name='Lanre',
            invitee_email='lanre@example.com',
            invitee_timezone='America/New_York',
            idempotency_key='unique-key-001',
            invitee_notes=None,
            user=owner,
        )  
        booking_2, _ = BookingService.create_booking(
            start_time=start_time_before,
            end_time=end,
            event_type=event_type,
            invitee_name='Lanre',
            invitee_email='lanre@example.com',
            invitee_timezone='America/New_York',
            idempotency_key='unique-key-002',
            invitee_notes=None,
            user=owner,
        )  
        url = reverse('booking-list')
        response = auth_client.get(url, {'start_time_after': start_time_after.isoformat(), 'start_time_before': (start + timedelta(hours=2)).isoformat()})        
        assert response.status_code == 200
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['id'] == str(booking_1.id)

    def test_another_user_bookings_never_appear_in_the_response(self, auth_client, owner, event_type, other_user, other_event_type):
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
        booking, _ = BookingService.create_booking(
            start_time=start,
            end_time=end,
            event_type=other_event_type,
            invitee_name='Lanre',
            invitee_email='lanre@example.com',
            invitee_timezone='America/New_York',
            idempotency_key='unique-key-002',
            invitee_notes=None,
            user=other_user,
        )  
        url = reverse('booking-list')
        response = auth_client.get(url, format='json')
        assert response.status_code == 200
        assert len(response.data['results']) == 1  
