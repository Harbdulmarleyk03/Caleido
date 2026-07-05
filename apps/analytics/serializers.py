from rest_framework import serializers


class AnalyticsResponseSerializer(serializers.Serializer):
    total_bookings = serializers.IntegerField()
    cancelled_bookings = serializers.IntegerField(required=False)
    avg_duration_minutes = serializers.FloatField(required=False)
    period = serializers.CharField()
