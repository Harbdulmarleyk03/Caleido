from datetime import timedelta
from apps.bookings.models import Booking, Invitee, BookingAudit, BookingAnswer
from rest_framework import serializers
from django.utils import timezone

class InviteeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitee
        fields = ['booking', 'name', 'email', 'timezone', 'locale', 'notes']

class CreateBookingSerializer(serializers.ModelSerializer):
    invitee_name = serializers.CharField()
    invitee_email = serializers.EmailField()
    invitee_timezone = serializers.CharField()
    invitee_notes = serializers.CharField(required=False,  allow_null=True, allow_blank=True)
    idempotency_key = serializers.CharField()
    class Meta:
        model = Booking
        fields = ['event_type', 'start_time', 'invitee_name', 'invitee_email', 'invitee_timezone', 'invitee_notes', 'idempotency_key']
    
    def validate(self, data):
       start = data.get('start_time')
       event_type = data.get('event_type')
       end = start + timedelta(minutes=event_type.duration_minutes)
       data['end_time'] = end

       if start < timezone.now():
           raise serializers.ValidationError("Cannot book a slot in the past.")
       
       overlapping = Booking.objects.filter(event_type=event_type, status = "confirmed", start_time__lt=end, end_time__gt=start)

       if overlapping.exists():
           raise serializers.ValidationError("This time slot is already booked.")
       
       return data 

class BookingAuditSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingAudit
        fields = ['booking', 'action', 'previous_data', 'changed_at', 'changed_by']

class BookingAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = BookingAnswer
        fields = "__all__"