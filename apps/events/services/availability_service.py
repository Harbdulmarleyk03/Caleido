from apps.events.models import AvailabilityRule


class AvailabilityRuleService:
    @staticmethod
    def create_availability_rule(event_type, validated_data: dict) -> AvailabilityRule:
        return AvailabilityRule.objects.create(event_type=event_type, **validated_data)
