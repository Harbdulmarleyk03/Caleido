import django_filters
from apps.bookings.models import Booking


class BookingFilter(django_filters.FilterSet):
    status = django_filters.CharFilter(field_name="status")
    start_time_after = django_filters.DateTimeFilter(
        field_name="start_time", lookup_expr="gte"
    )
    start_time_before = django_filters.DateTimeFilter(
        field_name="start_time", lookup_expr="lte"
    )
    event_type_id = django_filters.UUIDFilter(field_name="event_type__id")

    class Meta:
        model = Booking
        fields = ["status", "event_type_id"]
