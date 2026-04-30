from apps.events.models import EventType
from rest_framework import serializers 

class EventTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType 
        fields = "__all__"

class EventTypeDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType 
        fields = ['owner', 'title', 'team', 'description', 'duration_minutes', 'location_time', 
                  'location_value', 'assignment_rule', 'buffer_before_min', 'buffer_after_min', 
                  'min_notice_hours', 'max_future_days']

class EventTypeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType 
        fields = ['owner', 'title', 'team', 'description', 'duration_minutes', 'location_time', 
                  'location_value', 'assignment_rule', 'buffer_before_min', 'buffer_after_min', 
                  'min_notice_hours', 'max_future_days']
            
class EventTypeListSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventType 
        fields = ['owner', 'title', 'team', 'duration_minutes', 'location_time']

