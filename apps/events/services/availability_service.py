from apps.events.models import AvailabilityRule

class AvailabilityScheduleService:
    @staticmethod
    def create_availability_schedule(event_type, day_of_week, start_time, end_time):  
        overlapping = AvailabilityRule.objects.filter(
            event_type=event_type, day_of_week=day_of_week, start_time__lt=end_time, end_time__gt=start_time,).exists()
        if overlapping:
            raise ValueError("This time window overlaps with an existing rule")      
        if start_time < end_time:
            availability_schedule = AvailabilityRule.objects.create(
                event_type=event_type,
                day_of_week=day_of_week,
                start_time=start_time,
                end_time=end_time,
            )
            return availability_schedule
        else:
            raise ValueError("Start time must occur before end time")
    
    @staticmethod
    def update_availability_schedule(availability_rule_id, day_of_week, start_time, end_time):
        availability_schedule = AvailabilityRule.objects.get(id=availability_rule_id)
        availability_schedule.day_of_week = day_of_week
        availability_schedule.start_time = start_time
        availability_schedule.end_time = end_time
        availability_schedule.save()
        return availability_schedule