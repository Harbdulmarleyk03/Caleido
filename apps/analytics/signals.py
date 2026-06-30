import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from apps.bookings.models import Booking
from apps.analytics.cache import build_analytics_cache_key, PERIODS

logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=Booking)
def invalidate_owner_analytics_cache(sender, instance, **kwargs):
    owner_id = instance.event_type.owner_id
    for period in PERIODS:
        cache.delete(build_analytics_cache_key(owner_id=owner_id, period=period))
