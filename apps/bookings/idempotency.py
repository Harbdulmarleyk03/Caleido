from django.core.cache import cache
from apps.bookings.services import BookingService
from common.exceptions import ConflictError

CACHE_TIMEOUT = 300

def build_booking_cache_key(idempotency_key, user_id):
    return f"idempotency:{user_id}:{idempotency_key}"

def create_booking_in_redis(idempotency_key, user_id):
    cache_key = build_booking_cache_key(idempotency_key=idempotency_key, user_id=user_id)

    cached_create = cache.add(cache_key, "IN_PROGRESS", timeout=CACHE_TIMEOUT)

    if cached_create is True:
        try:
            booking = BookingService.create_booking(idempotency_key, user_id)
            cached_result = cache.set(cache_key, booking.id)
            return cached_result
        except Exception:
            cache.delete(cache_key)
            raise ConflictError("The slot is already taken") 
    
    cached_value = cache.get(cache_key)

    return cached_value
