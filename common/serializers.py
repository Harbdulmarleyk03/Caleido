import pytz
from rest_framework import serializers

class TimezoneField(serializers.CharField):
    """
    Validates that a string is a valid IANA timezone name.
    Used on User.timezone, Invitee.timezone, slot requests.

    Valid:   'Africa/Lagos', 'UTC', 'America/New_York'
    Invalid: 'Lagos', 'GMT+1', 'random string'
    """
    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        if value not in pytz.all_timezones:
            raise serializers.ValidationError(
                f"'{value}' is not a valid timezone. "
                f"Use an IANA timezone name e.g. 'Africa/Lagos'.")
        return value
    

class AwareDateTimeField(serializers.DateTimeField):
    """
    Enforces that incoming datetimes are timezone-aware.
    Rejects naive datetimes (those without timezone info).

    Valid:   '2025-04-06T10:00:00+01:00'
    Invalid: '2025-04-06T10:00:00' (no timezone offset)
    """
    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        if value.tzinfo is None:
            raise serializers.ValidationError(
                "Datetime must be timezone-aware. "
                "Include a UTC offset e.g. '2025-04-06T10:00:00+01:00'.")
        return value
    
class ReadWriteSerializerMixin:
    """
    Mixin for ViewSets that need different serializers
    for read vs write operations.

    In your ViewSet:
        class BookingViewSet(ReadWriteSerializerMixin, viewsets.ModelViewSet):
            read_serializer_class  = BookingDetailSerializer
            write_serializer_class = CreateBookingSerializer
    """
    read_serializer_class = None
    write_serializer_class = None

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return self.read_serializer_class
        return self.write_serializer_class