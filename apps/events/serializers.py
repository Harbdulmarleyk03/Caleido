from apps.events.models import EventType, AvailabilityRule, DateOverride
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

    def validate(self, data):
        if data['start_time'] >= data['end_time']:
            raise serializers.ValidationError('Start time must occur before end time')
        event_type = self.context.get('event_type')
        if event_type:
            overlapping = AvailabilityRule.objects.filter(
                event_type=event_type,
                day_of_week=data['day_of_week'],
                start_time__lt=data['end_time'],   # existing rule starts before new one ends
                end_time__gt=data['start_time'],   # existing rule ends after new one starts
            )
            # Exclude current instance on updates (PATCH/PUT)
            if self.instance:
                overlapping = overlapping.exclude(pk=self.instance.pk)

            if overlapping.exists():
                raise serializers.ValidationError("This time window overlaps with an existing rule.")
        return data
    
class DateOverrideSerializer(serializers.ModelSerializer):
    class Meta:
        model = DateOverride
        fields = ['specific_date', 'is_unavailable', 'custom_start', 'custom_end']
        read_only_fields = ['event_type']

    def validate(self, data):
        is_unavailable = data.get('is_unavailable')
        if is_unavailable == False:
            custom_start = data.get('custom_start')
            custom_end = data.get('custom_end')
            if custom_start is None or custom_end is None:
                raise serializers.ValidationError("Start time and end time are required when is_unavailable is False")
            if data['custom_start'] >= data['custom_end']:
                raise serializers.ValidationError('Start time must occur before end time')
            
        event_type = self.context.get('event_type')
        if event_type:
            overlapping = DateOverride.objects.filter(
                event_type=event_type,
                specific_date=data['specific_date'],
                is_unavailable=False,
                custom_start__lt=data['custom_end'],
                custom_end__gt=data['custom_start'],
            )

            if self.instance:
                overlapping = overlapping.exclude(pk=self.instance.pk)
            
            if overlapping.exists():
                raise serializers.ValidationError("This time window overlaps with an existing rule.")
        
            existing = DateOverride.objects.filter(
                event_type=event_type,
                specific_date=data['specific_date']
            )

            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise serializers.ValidationError("An override already exists for this date.")

        return data 
