from apps.events.models import AvailabilityRule
from apps.events.models import EventType

class AvailabilityScheduleService:
    def create_availability_schedule(self, event_type, day_of_week, start_time, end_time):
        if start_time < end_time:
            availability_schedule = AvailabilityRule.objects.create(
                event_type=event_type,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
            )
            availability_schedule.save()
            return availability_schedule
        else:
            raise ValueError("Start time must occur before end time")
        
    def update_availability_schedule(self, event_type_id, day_of_week, start_time, end_time):
        availability_schedule = AvailabilityRule.objects.get(id=event_type_id)
        availability_schedule.day_of_week = 3
        availability_schedule.start_time = 9
        availability_schedule.end_time = 12
        availability_schedule.save()
        return availability_schedule