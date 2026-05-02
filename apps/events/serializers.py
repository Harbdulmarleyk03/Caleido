from apps.events.models import EventType, AvailabilityRule
from rest_framework import serializers 

class EventTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType 
        fields = "__all__"
        read_only_fields = ['owner', 'slug', 'created_at', 'updated_at']

class EventTypeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType 
        fields = ['owner', 'title', 'team', 'description', 'duration_minutes', 'location_type', 
                  'location_value', 'assignment_rule', 'buffer_before_min', 'buffer_after_min', 
                  'min_notice_hours', 'max_future_days']

class EventTypeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType 
        fields = ['title', 'team', 'description', 'duration_minutes', 'location_type', 
                  'location_value', 'assignment_rule', 'buffer_before_min', 'buffer_after_min', 
                  'min_notice_hours', 'max_future_days']
            
class EventTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType 
        fields = ['id', 'is_active', 'owner', 'title', 'team', 'duration_minutes', 'location_type']

class AvailabilityRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = AvailabilityRule
        fields = ['event_type', 'day_of_week', 'start_time', 'end_time']
        read_only_fields = ['event_type']
