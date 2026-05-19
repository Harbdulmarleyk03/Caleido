from apps.bookings.models import Booking
from rest_framework import serializers

class CreateBookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['event_type', 'assigned_to', 'start_time', 'end_time', 'status',
                  'google_event_id', 'google_meet_link', 'stripe_payment']