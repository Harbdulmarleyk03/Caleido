from datetime import date, time, datetime
import pytz 

def get_availability_window(rules, target_date: date, owner_timezone: str):
    tz = pytz.timezone(owner_timezone)

    for rule in rules:
        if rule['day_of_week'] == target_date.weekday():
            # Combine date + time, localize to owner tz, then convert to UTC
            start_local = tz.localize(datetime.combine(target_date, rule['start_time']))
            end_local = tz.localize(datetime.combine(target_date, rule['end_time']))

            return start_local.astimezone(pytz.UTC), end_local.astimezone(pytz.UTC)
        
        return None, None
    
def apply_date_overrides(overrides, date, owner_timezone: str):
    tz = pytz.timezone(owner_timezone)


def generate_candidate_slots(window_start, window_end, duration_minutes):
    pass 