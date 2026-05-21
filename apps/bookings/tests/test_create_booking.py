from urllib import response

import pytest
from apps.bookings.services import BookingService
from django.urls import reverse
from rest_framework.test import APIClient
from apps.events.models import EventType
from apps.users.tests.factories import UserFactory
from datetime import datetime
import pytz

@pytest.fixture
def owner(db):
    return UserFactory(is_verified=True)

@pytest.fixture
def event_type(owner):
    return EventType.objects.create(
        owner=owner,
        title="Test Event",
        slug="test-event",
        duration_minutes=30,
        location_type='zoom',
        min_notice_hours=0,
        max_future_days=60,
        buffer_before_min=0,
        buffer_after_min=0,
    )

start = datetime(2026, 5, 21, 9, 0, tzinfo=pytz.UTC)
end = datetime(2026, 5, 21, 9, 30, tzinfo=pytz.UTC)

@pytest.mark.django_db
class TestCreateBookingView:

    def test_create_booking(self, event_type, api_client):
        data = {
            'start_time': "2026-05-21T09:00:00Z",
            'event_type': str(event_type.id),
            'invitee_name': 'Karl',
            'invitee_email': 'karl@example.com',
            'invitee_timezone': 'Africa/Lagos',
            'idempotency_key': 'unique-key-001',
            'invitee_notes': None,
        }
        url = reverse('booking-list')
        response = api_client.post(url, data, format='json')
        print(response.data)
        assert response.status_code == 201 

    def test_duplicate_idempotency_key(self, event_type, owner, api_client):
        BookingService.create_booking(
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
        data = {
            'start_time': "2026-05-21T09:00:00Z",
            'event_type': str(event_type.id),
            'invitee_name': 'Karl',
            'invitee_email': 'karl@example.com',
            'invitee_timezone': 'Africa/Lagos',
            'idempotency_key': 'unique-key-001',
            'invitee_notes': None,
        }

        url = reverse('booking-list')
        response = api_client.post(url, data, format='json')
        assert response.status_code == 200
        assert 'id' in response.data 

    def test_conflicting_slots(self, event_type, owner, api_client):
        BookingService.create_booking(
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
        data = {
            'start_time': "2026-05-21T09:15:00Z",
            'event_type': str(event_type.id),
            'invitee_name': 'Karl',
            'invitee_email': 'karl@example.com',
            'invitee_timezone': 'Africa/Lagos',
            'idempotency_key': 'unique-key-002',
            'invitee_notes': None,
        }
        url = reverse('booking-list')
        response = api_client.post(url, data, format='json')
        assert response.status_code == 409
        assert "The slot is already taken." in str(response.data)

    def test_missing_required_fields(self, api_client):
        data = {
            'start_time': "2026-05-21T09:00:00Z",
            'invitee_name': 'Karl',
            'invitee_email': 'karl@example.com',
            'invitee_timezone': 'Africa/Lagos',
            'idempotency_key': 'unique-key-003',
            'invitee_notes': None,
        }

        url = reverse('booking-list')
        response = api_client.post(url, data, format='json')
        assert response.status_code == 400
        assert "event_type" in response.data['details']

    def test_past_slots(self, event_type, owner, api_client):
        
        current_slot = {
            'start_time': '2024-01-01T09:00:00Z',  # clearly in the past
            'event_type': str(event_type.id),
            'invitee_name': 'Karl',
            'invitee_email': 'karl@example.com',
            'invitee_timezone': 'Africa/Lagos',
            'idempotency_key': 'unique-key-004',
            'invitee_notes': None,
        }
        url = reverse('booking-list')
        response = api_client.post(url, current_slot, format='json')
        assert response.status_code == 400
        assert "Cannot book a slot in the past." in str(response.data)

