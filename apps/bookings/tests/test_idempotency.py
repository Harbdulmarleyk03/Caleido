# apps/bookings/tests/test_idempotency.py

import pytest
from unittest.mock import MagicMock, patch
from django.core.cache import cache

from apps.bookings.idempotency import (
    create_booking_in_redis,
    build_booking_cache_key,
    IN_PROGRESS_TIMEOUT,
    CACHE_TIMEOUT,
)
from common.exceptions import ConflictError
from apps.bookings.tests.factories import BookingFactory
from apps.users.tests.factories import UserFactory


@pytest.mark.django_db
class TestBuildBookingCacheKey:

    def test_key_format(self):
        key = build_booking_cache_key(idempotency_key="abc-123", user_id="user-456")
        assert key == "idempotency:user-456:abc-123"

    def test_different_users_produce_different_keys(self):
        key_a = build_booking_cache_key(idempotency_key="abc-123", user_id="user-1")
        key_b = build_booking_cache_key(idempotency_key="abc-123", user_id="user-2")
        assert key_a != key_b

    def test_different_idempotency_keys_produce_different_keys(self):
        key_a = build_booking_cache_key(idempotency_key="key-1", user_id="user-1")
        key_b = build_booking_cache_key(idempotency_key="key-2", user_id="user-1")
        assert key_a != key_b


@pytest.mark.django_db
class TestCreateBookingInRedis:

    def test_first_request_calls_create_booking_and_returns_booking(self):
        user = UserFactory()
        booking = BookingFactory()
        idempotency_key = "unique-key-001"

        create_booking = MagicMock(return_value=booking)

        result = create_booking_in_redis(
            idempotency_key=idempotency_key,
            user_id=str(user.id),
            create_booking=create_booking,
        )

        create_booking.assert_called_once_with()
        assert result == booking

    def test_first_request_stores_booking_id_in_cache(self):
        user = UserFactory()
        booking = BookingFactory()
        idempotency_key = "unique-key-002"
        key = build_booking_cache_key(idempotency_key=idempotency_key, user_id=str(user.id))

        create_booking = MagicMock(return_value=booking)

        create_booking_in_redis(
            idempotency_key=idempotency_key,
            user_id=str(user.id),
            create_booking=create_booking,
        )

        # After success, cache holds booking.id with long TTL — not "IN_PROGRESS"
        assert cache.get(key) == booking.id

    def test_duplicate_request_with_completed_key_returns_same_booking(self):
        user = UserFactory()
        booking = BookingFactory()
        idempotency_key = "unique-key-003"
        key = build_booking_cache_key(idempotency_key=idempotency_key, user_id=str(user.id))

        # Simulate a completed prior request — cache holds the booking id
        cache.set(key, booking.id, timeout=CACHE_TIMEOUT)

        create_booking = MagicMock()

        result = create_booking_in_redis(
            idempotency_key=idempotency_key,
            user_id=str(user.id),
            create_booking=create_booking,
        )

        create_booking.assert_not_called()
        assert result.id == booking.id

    def test_duplicate_request_while_in_progress_raises_conflict(self):
        user = UserFactory()
        idempotency_key = "unique-key-004"
        key = build_booking_cache_key(idempotency_key=idempotency_key, user_id=str(user.id))

        # Simulate another request already holding the lock
        cache.set(key, "IN_PROGRESS", timeout=IN_PROGRESS_TIMEOUT)

        create_booking = MagicMock()

        with pytest.raises(ConflictError):
            create_booking_in_redis(
                idempotency_key=idempotency_key,
                user_id=str(user.id),
                create_booking=create_booking,
            )

        create_booking.assert_not_called()

    def test_expired_key_none_raises_conflict(self):
        """None in cache covers the race window where the key expired
        between cache.add() returning False and cache.get() reading it."""
        user = UserFactory()
        idempotency_key = "unique-key-005"
        build_booking_cache_key(idempotency_key=idempotency_key, user_id=str(user.id))

        # cache.add() will fail because key exists, then cache.get() returns None
        # Simulate: key exists (so add fails) but get returns None (expired race)
        with patch("apps.bookings.idempotency.cache") as mock_cache:
            mock_cache.add.return_value = False
            mock_cache.get.return_value = None

            with pytest.raises(ConflictError):
                create_booking_in_redis(
                    idempotency_key=idempotency_key,
                    user_id=str(user.id),
                    create_booking=MagicMock(),
                )

    def test_exception_in_create_booking_deletes_cache_key_and_reraises(self):
        user = UserFactory()
        idempotency_key = "unique-key-006"
        key = build_booking_cache_key(idempotency_key=idempotency_key, user_id=str(user.id))

        create_booking = MagicMock(side_effect=ValueError("DB exploded"))

        with pytest.raises(ValueError, match="DB exploded"):
            create_booking_in_redis(
                idempotency_key=idempotency_key,
                user_id=str(user.id),
                create_booking=create_booking,
            )

        # Key must be cleaned up so the next retry can proceed
        assert cache.get(key) is None

    def test_exception_does_not_raise_conflict_error(self):
        """Bare raise must re-raise original exception — never swallow into ConflictError."""
        user = UserFactory()
        idempotency_key = "unique-key-007"

        create_booking = MagicMock(side_effect=RuntimeError("unexpected"))

        with pytest.raises(RuntimeError):
            create_booking_in_redis(
                idempotency_key=idempotency_key,
                user_id=str(user.id),
                create_booking=create_booking,
            )

    def test_two_different_users_same_idempotency_key_are_independent(self):
        """Keys are namespaced by user_id — one user's key must not block another."""
        user_a = UserFactory()
        user_b = UserFactory()
        booking_a = BookingFactory()
        booking_b = BookingFactory()
        idempotency_key = "shared-key"

        result_a = create_booking_in_redis(
            idempotency_key=idempotency_key,
            user_id=str(user_a.id),
            create_booking=MagicMock(return_value=booking_a),
        )
        result_b = create_booking_in_redis(
            idempotency_key=idempotency_key,
            user_id=str(user_b.id),
            create_booking=MagicMock(return_value=booking_b),
        )

        assert result_a.id == booking_a.id
        assert result_b.id == booking_b.id