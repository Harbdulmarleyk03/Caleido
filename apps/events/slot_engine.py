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
    
def apply_date_override(overrides, date, owner_timezone: str):
    tz = pytz.timezone(owner_timezone)

    for override in overrides:
        if override['specific_date'] != date:
            continue
        if not override['is_unavailable']: 
            custom_start_local = tz.localize(datetime.combine(date, override['custom_start']))
            custom_end_local = tz.localize(datetime.combine(date, override['custom_end']))

            return custom_start_local.astimezone(pytz.UTC), custom_end_local.astimezone(pytz.UTC)
            
        else:
            return None, None

    return None

def generate_candidate_slots(window_start, window_end, duration_minutes):
    pass 

def filter_by_notice_and_future(slots, min_notice_hours, max_future_days, date):
    pass 

def filter_by_bookings(slots, bookings, buffer_before, buffer_after):
    pass 

def convert_slots_to_timezone(slots, timezone):
    pass 

def generate_slots():
    pass

