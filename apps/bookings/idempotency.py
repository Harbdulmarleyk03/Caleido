from django.core.cache import cache
from common.exceptions import ConflictError
from apps.bookings.models import Booking

IN_PROGRESS_TIMEOUT = 30
CACHE_TIMEOUT = 600


def build_booking_cache_key(idempotency_key, user_id):
    return f"idempotency:{user_id}:{idempotency_key}"


def create_booking_in_redis(idempotency_key, user_id, create_booking):
    cache_key = build_booking_cache_key(
        idempotency_key=idempotency_key, user_id=user_id
    )

    cached_create = cache.add(cache_key, "IN_PROGRESS", timeout=IN_PROGRESS_TIMEOUT)

    if cached_create is True:
        try:
            booking = create_booking()
            cache.set(cache_key, booking.id, timeout=CACHE_TIMEOUT)
            return booking
        except Exception:
            cache.delete(cache_key)
            raise

    cached_value = cache.get(cache_key)

    if cached_value in ("IN_PROGRESS", None):
        raise ConflictError(
            "A request with this idempotency key is already being processed."
        )

    return Booking.objects.get(id=cached_value)
