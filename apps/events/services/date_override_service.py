from apps.events.models import DateOverride

class DateOverrideService:
    @staticmethod
    def create_date_override(event_type, validated_data: dict) -> DateOverride:
        return DateOverride.objects.create(event_type=event_type, **validated_data)