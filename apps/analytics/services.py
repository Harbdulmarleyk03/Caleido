from django.db.models import Count, F 
from apps.bookings.models import Booking
from apps.analytics.cache import build_analytics_cache_key
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
        
        except:
            logger.error("Failed to read owner's analytics cache", {"cache_key": cache_key})
        
        total_bookings = list(Booking.objects.filter(event_type__owner=owner).aggregate(total=Count('id')))
        status = list(Booking.objects.filter(event_type__owner=owner).values("status").annotate(total=Count('id')))

        total = Booking.objects.filter(event_type__owner=owner).count()
        try:
            cancelled = Booking.objects.filter(event_type__owner=owner, status="cancelled").count()
            cancellation_rate = (cancelled / total) * 100
        except ZeroDivisionError:
            cancellation_rate = 0

        daily_bookings = list(Booking.objects.filter(event_type__owner=owner).annotate(day=TruncDay('created_at')).values('day').annotate(total=Count('id')).order_by('day'))
        weekly_bookings = list(Booking.objects.filter(event_type__owner=owner).annotate(week=TruncWeek('created_at')).values('week').annotate(total=Count('id')).order_by('week'))
        monthly_bookings = list(Booking.objects.filter(event_type__owner=owner).annotate(month=TruncMonth('created_at')).values('month').annotate(total=Count('id')).order_by('month'))
        event_type_popularity = list(EventType.objects.filter(event_type__owner=owner).annotate(booking_count=Count('bookings')))
        average_lead_time = Booking.objects.filter(event_type__owner=owner).aggregate(average_lead_time=F('start_time') - F('created_at'))

        analytics = {'total_bookings': total_bookings, 'cancellation_rate': cancellation_rate, 'daily_bookings': daily_bookings,
                     'weekly_bookings': weekly_bookings, 'monthly_bookings': monthly_bookings, 'event_type_popularity': event_type_popularity,
                     'average_lead_time': average_lead_time}

        try: 
            cache.set(cache_key, analytics, timeout=CACHE_TIMEOUT)
        except:
            logger.error("Failed to write owner's analytics cache", {'cache_key': cache_key})
        return analytics