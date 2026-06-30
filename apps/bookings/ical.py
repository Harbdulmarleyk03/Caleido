from icalendar import Calendar, Event
from django.conf import settings
from django.utils import timezone

class IcalExportService:

    @staticmethod
    def generate_booking_ical(booking):
        calendar = Calendar()
        event = Event()
        event.add('summary', booking.event_type.title)
        event.add('description', booking.event_type.description)
        if booking.event_type.location_value is not None:
            event.add('location', booking.event_type.location_value)
        event.add('dtstart', booking.start_time)
        event.add('dtend', booking.end_time)
        event.add('uid', f"{booking.id}@{settings.ICAL_UID_DOMAIN}")
        event.add('status', 'CONFIRMED' if booking.status == 'confirmed' else 'CANCELLED')
        event.add('dtstamp', timezone.now())

        calendar.add_component(event)
        ical_content = calendar.to_ical()
        return ical_content
       