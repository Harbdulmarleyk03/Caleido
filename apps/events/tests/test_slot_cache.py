import pytest
from django.core.cache import cache
from django.utils import timezone as tz
from unittest.mock import MagicMock
from datetime import timedelta

from apps.events.services.slot_cache_service import SlotCacheService
from apps.events.cache import build_slot_cache_key
from apps.events.tests.factories import EventTypeFactory
from apps.bookings.tests.factories import BookingFactory
from apps.bookings.services import BookingService


@pytest.mark.django_db(transaction=True)
class TestSlotCacheService:

    def test_cache_miss_computes_and_stores(self):
        booking = BookingFactory()
        owner_tz = booking.event_type.owner.timezone
        date = booking.start_time.date().isoformat()
        key = build_slot_cache_key(
            event_type_id=booking.event_type_id,
            date=date,
            timezone=owner_tz,
        )
        assert cache.get(key) is None

        expected_slots = [
            {"start": "09:00", "end": "09:30"},
            {"start": "10:00", "end": "10:30"},
        ]
        generate_slots = MagicMock(return_value=expected_slots)

        result = SlotCacheService.get_slots(
            event_type_id=booking.event_type_id,
            date=date,
            timezone=owner_tz,
            generate_slots=generate_slots,
        )

        generate_slots.assert_called_once_with()
        assert result == expected_slots
        assert cache.get(key) == expected_slots

    def test_cache_hit_skips_computation(self):
        booking = BookingFactory()
        owner_tz = booking.event_type.owner.timezone
        date = booking.start_time.date().isoformat()
        known_value = [{"start": "09:00", "end": "09:30"}]
        key = build_slot_cache_key(
            event_type_id=booking.event_type_id,
            date=date,
            timezone=owner_tz,
        )
        cache.set(key, known_value)

        generate_slots = MagicMock(return_value=[{"start": "10:00", "end": "10:30"}])

        result = SlotCacheService.get_slots(
            event_type_id=booking.event_type_id,
            date=date,
            timezone=owner_tz,
            generate_slots=generate_slots,
        )

        generate_slots.assert_not_called()
        assert result == known_value

    def test_empty_list_is_cached_and_not_recomputed(self):
        booking = BookingFactory()
        owner_tz = booking.event_type.owner.timezone
        date = booking.start_time.date().isoformat()
        key = build_slot_cache_key(
            event_type_id=booking.event_type_id,
            date=date,
            timezone=owner_tz,
        )
        cache.set(key, [])

        generate_slots = MagicMock(return_value=[{"start": "09:00", "end": "09:30"}])

        result = SlotCacheService.get_slots(
            event_type_id=booking.event_type_id,
            date=date,
            timezone=owner_tz,
            generate_slots=generate_slots,
        )

        generate_slots.assert_not_called()
        assert result == []

    def test_create_booking_invalidates_slot_cache(self):
        event_type = EventTypeFactory()
        owner_tz = event_type.owner.timezone
        start_time = tz.now() + timedelta(days=1)
        date = start_time.date().isoformat()

        key = build_slot_cache_key(
            event_type_id=event_type.id,
            date=date,
            timezone=owner_tz,
        )
        # Prime FIRST — then trigger the signal
        cache.set(key, ["cached_value"])
        assert cache.get(key) == ["cached_value"]

        BookingFactory(event_type=event_type, start_time=start_time)

        assert cache.get(key) is None

    def test_reschedule_booking_invalidates_old_and_new_slot_cache(self):
        booking = BookingFactory()
        owner_tz = booking.event_type.owner.timezone

        old_date = booking.start_time.date().isoformat()
        old_key = build_slot_cache_key(
            event_type_id=booking.event_type_id,
            date=old_date,
            timezone=owner_tz,
        )
        cache.set(old_key, ["old_cached"])

        new_start_time = booking.start_time + timedelta(days=1)
        new_end_time = new_start_time + timedelta(
            minutes=booking.event_type.duration_minutes
        )
        new_date = new_start_time.date().isoformat()
        new_key = build_slot_cache_key(
            event_type_id=booking.event_type_id,
            date=new_date,
            timezone=owner_tz,
        )
        cache.set(new_key, ["new_cached"])

        BookingService.reschedule_booking(
            booking=booking,
            user=booking.event_type.owner,  # authenticated owner — satisfies audit_user
            start_time=new_start_time,
            end_time=new_end_time,
        )

        assert cache.get(old_key) is None
        assert cache.get(new_key) is None
