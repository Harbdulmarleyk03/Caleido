from django.db.models import Count, F, Avg, ExpressionWrapper, DurationField
from apps.bookings.models import Booking
from apps.analytics.cache import build_analytics_cache_key, get_period_cutoff
from django.core.cache import cache
import logging
from django.db.models.functions import TruncDay, TruncWeek, TruncMonth
from apps.events.models import EventType

logger = logging.getLogger(__name__)

CACHE_TIMEOUT = 600


class AnalyticService:

    @staticmethod
    def get_owner_analytics(owner, period):
        cache_key = build_analytics_cache_key(owner_id=owner.id, period=period)

        try:
            _MISS = object()
            cached_result = cache.get(cache_key, _MISS)

            if cached_result is not _MISS:
                return cached_result

        except Exception:
            logger.exception(
                "Failed to read owner's analytics cache", extra={"cache_key": cache_key}
            )

        cutoff = get_period_cutoff(period)
        base_qs = Booking.objects.filter(event_type__owner=owner)
        if cutoff is not None:
            base_qs = base_qs.filter(created_at__gte=cutoff)

        status = list(base_qs.values("status").annotate(total=Count("id")))

        total = base_qs.count()
        try:
            cancelled = base_qs.filter(status="cancelled").count()
            cancellation_rate = (cancelled / total) * 100
        except ZeroDivisionError:
            cancellation_rate = 0

        daily_bookings = list(
            base_qs.annotate(day=TruncDay("created_at"))
            .values("day")
            .annotate(total=Count("id"))
            .order_by("day")
        )
        weekly_bookings = list(
            base_qs.annotate(week=TruncWeek("created_at"))
            .values("week")
            .annotate(total=Count("id"))
            .order_by("week")
        )
        monthly_bookings = list(
            base_qs.annotate(month=TruncMonth("created_at"))
            .values("month")
            .annotate(total=Count("id"))
            .order_by("month")
        )
        event_type_popularity = list(
            EventType.objects.filter(owner=owner)
            .annotate(booking_count=Count("bookings"))
            .values("id", "title", "booking_count")
        )
        lead_time_result = base_qs.aggregate(
            average_lead_time=Avg(
                ExpressionWrapper(
                    F("start_time") - F("created_at"), output_field=DurationField()
                )
            )
        )
        avg_delta = lead_time_result["average_lead_time"]
        average_lead_time_hours = (
            avg_delta.total_seconds() / 3600 if avg_delta else None
        )

        analytics = {
            "total_bookings": total,
            "cancellation_rate": cancellation_rate,
            "daily_bookings": daily_bookings,
            "weekly_bookings": weekly_bookings,
            "monthly_bookings": monthly_bookings,
            "event_type_popularity": event_type_popularity,
            "average_lead_time": average_lead_time_hours,
            "status": status,
        }

        try:
            cache.set(cache_key, analytics, timeout=CACHE_TIMEOUT)
        except Exception:
            logger.exception(
                "Failed to write owner's analytics cache",
                extra={"cache_key": cache_key},
            )
        return analytics
