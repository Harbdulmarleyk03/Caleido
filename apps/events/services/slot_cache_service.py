import logging
from django.core.cache import cache
from apps.events.cache import build_slot_cache_key

logger = logging.getLogger(__name__)

CACHE_TIMEOUT = 60


class SlotCacheService:
    @staticmethod
    def get_slots(*, event_type_id, date, timezone, generate_slots):
        cache_key = build_slot_cache_key(
            event_type_id=event_type_id, date=date, timezone=timezone
        )
        try:
            _MISS = object()
            cached_result = cache.get(cache_key, _MISS)
            if cached_result is not _MISS:
                return cached_result
        except Exception:
            logger.exception(
                "Failed to read slot cache", extra={"cache_key": cache_key}
            )

        slots = generate_slots()

        try:
            cache.set(cache_key, slots, timeout=CACHE_TIMEOUT)
        except Exception:
            logger.exception(
                "Failed to write slot cache",
                extra={"cache_key": cache_key},
            )
        return slots
