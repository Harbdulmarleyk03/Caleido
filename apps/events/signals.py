import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from apps.bookings.models import Booking
from apps.events.cache import build_slot_cache_key
from apps.bookings.models import BookingAudit
from datetime import datetime

logger = logging.getLogger(__name__)

@receiver([post_save, post_delete], sender=Booking)
def invalidate_slot_cache(sender, instance, **kwargs):
    owner_timezone = instance.event_type.owner.timezone
    cache.delete(build_slot_cache_key(event_type_id=instance.event_type_id, date=instance.start_time.date().isoformat(), timezone=owner_timezone))

    audit = BookingAudit.objects.filter(booking=instance, action='rescheduled').order_by("-changed_at").first()

    if audit and audit.previous_data:
        old_start = datetime.fromisoformat(audit.previous_data['start_time'])
        cache.delete(build_slot_cache_key(
            event_type_id=instance.event_type_id,
            date=old_start.date().isoformat(),
            timezone=owner_timezone
        ))
