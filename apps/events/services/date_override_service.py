from apps.events.models import DateOverride

class DateOverrideService:
    @staticmethod
    def create_date_override(event_type, validated_data):
        return DateOverride.objects.create(
            event_type=event_type,
            specific_date=validated_data['specific_date'],
            is_unavailable=validated_data['is_unavailable'],
            custom_start=validated_data['custom_start'],
            custom_end=validated_data['custom_end'],
        )