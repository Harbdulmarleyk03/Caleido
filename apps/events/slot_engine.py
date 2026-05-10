from datetime import date, time, datetime, timedelta
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

def generate_candidate_slots(window_start, window_end, duration_minutes: int):
    slots = []
    slot_start = window_start
    duration = timedelta(minutes=duration_minutes)
    slot_end = slot_start + duration

    while slot_end <= window_end:
        slots.append((slot_start, slot_end))
        slot_start += duration
        slot_end = slot_start + duration

    return slots

def filter_by_notice_and_future(slots, min_notice_hours, max_future_days, now, target_date: date):
    today = now.date()
   
    if target_date > today + timedelta(days=max_future_days):
        return []
        
    earliest_allowed = now + timedelta(hours=min_notice_hours)

    return [(start, end) for start, end in slots if start >= earliest_allowed]

def filter_by_bookings(slots, bookings, buffer_before: int, buffer_after: int):
    available_slots = []

    for slot_start, slot_end in slots:
        blocked = False
        for booking in bookings:
            booking_start = booking['start_time']
            booking_end = booking['end_time']
            blocked_start = booking_start - timedelta(minutes=buffer_before)
            blocked_end = booking_end + timedelta(minutes=buffer_after)

            if slot_start < blocked_end and slot_end > blocked_start:
                blocked = True
                break 
        if not blocked:
            available_slots.append((slot_start, slot_end))
    return available_slots

def convert_slots_to_timezone(slots, timezone: str):
    tz = pytz.timezone(timezone)
    return [
        {"start": slot_start.astimezone(tz).isoformat(), "end": slot_end.astimezone(tz).isoformat()}
        for slot_start, slot_end in slots]

def generate_slots(rules, overrides, bookings, target_date, timezone, 
                   duration, buffer_before, buffer_after, 
                   min_notice_hours, max_future_days, owner_timezone, now):
    
    window_start, window_end = get_availability_window(rules, target_date, owner_timezone)

    override = apply_date_override(overrides, target_date, owner_timezone)

    if override is not None:
        window_start, window_end = override

    if window_start is None:
        return []

    slots = generate_candidate_slots(window_start, window_end, duration)

    slots = filter_by_notice_and_future(slots, min_notice_hours, max_future_days, now, target_date)

    slots = filter_by_bookings(slots, bookings, buffer_before, buffer_after)

    return convert_slots_to_timezone(slots, timezone)

   