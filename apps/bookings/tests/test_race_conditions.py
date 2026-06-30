import pytest 
from apps.events.models import EventType
from apps.users.tests.factories import UserFactory
from django.urls import reverse
from django.utils import timezone
import pytz 
from datetime import timedelta, datetime
from apps.bookings.services import BookingService
import threading
from common.exceptions import ConflictError
from apps.bookings.models import Booking
from django.conf import settings

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

start = datetime(2026, 6, 15, 9, 0, tzinfo=pytz.UTC)
end = datetime(2026, 6, 15, 9, 30, tzinfo=pytz.UTC)
future_start = timezone.now() + timedelta(days=1)

class TestRaceConditions:

    def test_precedence_idempotency_key_header(self, event_type, api_client):
        data = {
            'start_time': future_start.isoformat(),
            'event_type': str(event_type.id),
            'invitee_name': 'Karl',
            'invitee_email': 'karl@example.com',
            'invitee_timezone': 'Africa/Lagos',
            'invitee_notes': None,
        }
          
        url = reverse('booking-list')
        response1 = api_client.post(url, data, format='json', HTTP_IDEMPOTENCY_KEY='unique-key-001')
        response2 = api_client.post(url, data, format='json', HTTP_IDEMPOTENCY_KEY='unique-key-001')

        assert response1.status_code == 201
        assert response2.status_code == 200
        assert Booking.objects.count() == 1
        assert response1.data['id'] == response2.data['id']

    def test_idempotency_key_work_as_fallback(self, event_type, api_client):
        data = {
            'start_time': future_start.isoformat(),
            'event_type': str(event_type.id),
            'invitee_name': 'Karl',
            'invitee_email': 'karl@example.com',
            'idempotency_key': 'unique-key-001',
            'invitee_timezone': 'Africa/Lagos',
            'invitee_notes': None,
        }
        url = reverse('booking-list')
        response1 = api_client.post(url, data, format='json',)
        response2 = api_client.post(url, data, format='json',)

        assert response1.status_code == 201
        assert response2.status_code == 200
        assert Booking.objects.count() == 1
        assert response1.data['id'] == response2.data['id']

    @pytest.mark.skipif('sqlite' in settings.DATABASES['default']['ENGINE'], reason="Requires PostgreSQL")
    @pytest.mark.django_db(transaction=True)    
    def test_concurrent_booking_conflict(self, owner, event_type):
        results = []
        errors = []
        barrier = threading.Barrier(2)

        def attempt_booking(key):
            barrier.wait()
            try:
                booking, created = BookingService.create_booking(    
                    start_time=start,
                    end_time=end,
                    event_type=event_type,
                    invitee_name='Lanre',
                    invitee_email='lanre@example.com',
                    invitee_timezone='America/New_York',
                    idempotency_key=key,
                    invitee_notes=None,
                    user=owner
                )
                results.append(created)
            except ConflictError:
                errors.append(True)
           
        t1 = threading.Thread(target=attempt_booking, args=('key-001',))
        t2 = threading.Thread(target=attempt_booking, args=('key-002',))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        assert len(results) == 1
        assert len(errors) == 1
        assert Booking.objects.count() == 1