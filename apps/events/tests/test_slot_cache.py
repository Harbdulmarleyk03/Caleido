import pytest 
from apps.events.services.slot_cache_service import SlotCacheService
from apps.events.cache import build_slot_cache_key
from django.core.cache import cache
from unittest.mock import MagicMock, patch
from apps.bookings.tests.factories import BookingFactory
from apps.bookings.services import BookingService
from datetime import timedelta

from apps.events.tests.factories import EventTypeFactory

@pytest.fixture
def generate_slots():
    return MagicMock(return_value=["09:00", "09:30"])

@pytest.fixture
def known_value():
    return [{"start": "09:00", "end": "09:30"}]

@pytest.mark.django_db(transaction=True)
class TestSlotCacheService:
    def test_cache_miss_computes_and_store(self, generate_slots):
        booking = BookingFactory()
        key = build_slot_cache_key(
            event_type_id=booking.event_type_id,
            date=booking.start_time.date().isoformat(),
            timezone=booking.event_type.owner.timezone,
        )
        assert cache.get(key) is None
        expected_slots = [
            {"start": "09:00", "end": "09:30"},
            {"start": "10:00", "end": "10:30"},
        ]
        generate_slots = MagicMock(return_value=expected_slots)
        result = SlotCacheService.get_slots(event_type_id=booking.event_type_id, date=booking.start_time.date().isoformat(), timezone="Africa/Lagos", generate_slots=generate_slots,)
        generate_slots.assert_called_once_with()
        # Returned value matches callable output
        assert result == expected_slots
        # Result was cached
        assert cache.get(key) == expected_slots

    def test_cache_hit_skips_computation(self, known_value, generate_slots):
        booking = BookingFactory()
        key = build_slot_cache_key(
            event_type_id=booking.event_type_id,
            date=booking.start_time.date().isoformat(),
            timezone=booking.event_type.owner.timezone,
        )        
        cache.set(key, known_value)
        expected_slots = [
            {"start": "09:00", "end": "09:30"},
            {"start": "10:00", "end": "10:30"},
        ]
        generate_slots = MagicMock(return_value=expected_slots)
        result = SlotCacheService.get_slots(event_type_id=booking.event_type_id, date=booking.start_time.date().isoformat(), timezone="Africa/Lagos", generate_slots=generate_slots,)
        generate_slots.assert_not_called()
        assert result == known_value
    
    def test_cached_and_not_recomputed_empty_list(self, generate_slots):
        booking = BookingFactory()
        key = build_slot_cache_key(
            event_type_id=booking.event_type_id,
            date=booking.start_time.date().isoformat(),
            timezone=booking.event_type.owner.timezone,
        )        
        cache.set(key, [])
        expected_slots = [
            {"start": "09:00", "end": "09:30"},
            {"start": "10:00", "end": "10:30"},
        ]
        generate_slots = MagicMock(return_value=expected_slots)
        result = SlotCacheService.get_slots(event_type_id=booking.event_type_id, date=booking.start_time.date().isoformat(), timezone="Africa/Lagos", generate_slots=generate_slots,)
        generate_slots.assert_not_called()
        assert result == []

    def test_create_booking_invalidation(self):
        event_type = EventTypeFactory()
        key = build_slot_cache_key(
            event_type_id=event_type.id,
            date=event_type.start_time.date().isoformat(),
            timezone=event_type.owner.timezone,
        )
        BookingFactory(event_type=event_type)
        cache.set(key, "cached_value")
        assert cache.get(key) is None 

    def test_reschedule_booking_invalidation(self):  
        booking = BookingFactory()
        old_key = build_slot_cache_key(
            event_type_id=booking.event_type_id,
            date=booking.start_time.date().isoformat(),
            timezone=booking.event_type.owner.timezone,
        )
        cache.set(old_key, ["cached"])
        new_start_time = booking.start_time + timedelta(days=1)

        BookingService.reschedule_booking(
            booking_id=booking.id,
            new_start_time=new_start_time,
        )
        new_key = build_slot_cache_key(
            event_type_id=booking.event_type_id,
            date=new_start_time.date().isoformat(),
            timezone=booking.event_type.owner.timezone,
        )
        assert cache.get(old_key) is None 
        assert cache.get(new_key) is None 

