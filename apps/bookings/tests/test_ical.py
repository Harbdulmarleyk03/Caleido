import pytest
from apps.bookings.tests.factories import BookingFactory
from apps.bookings.ical import IcalExportService
from apps.events.tests.factories import EventTypeFactory
from apps.users.tests.factories import UserFactory
import uuid
from icalendar import Calendar
from django.conf import settings


@pytest.fixture
def other_user(db):
    return UserFactory(is_verified=True)


@pytest.fixture
def owner(db):
    return UserFactory(is_verified=True)


@pytest.mark.django_db
class TestIcalExportService:

    def test_ical_contains_correct_summary(self, owner):
        event_type = EventTypeFactory(owner=owner)
        booking = BookingFactory(event_type=event_type)
        ical_content = IcalExportService.generate_booking_ical(booking)

        cal = Calendar.from_ical(ical_content)
        vevent = next(c for c in cal.walk() if c.name == "VEVENT")
        assert vevent.get("summary") == event_type.title

    def test_ical_contains_correct_dtstart_and_dtend(self, owner):
        event_type = EventTypeFactory(owner=owner)
        booking = BookingFactory(event_type=event_type)
        ical_content = IcalExportService.generate_booking_ical(booking)
        cal = Calendar.from_ical(ical_content)
        vevent = next(c for c in cal.walk() if c.name == "VEVENT")
        assert vevent.get("dtstart").dt == booking.start_time
        assert vevent.get("dtend").dt == booking.end_time

    def test_ical_contains_uid(self, owner):
        event_type = EventTypeFactory(owner=owner)
        booking = BookingFactory(event_type=event_type)
        ical_content = IcalExportService.generate_booking_ical(booking)
        cal = Calendar.from_ical(ical_content)
        vevent = next(c for c in cal.walk() if c.name == "VEVENT")
        assert vevent.get("uid") == f"{booking.id}@{settings.ICAL_UID_DOMAIN}"

    def test_cancelled_booking_has_cancelled_status(self, owner, api_client):
        event_type = EventTypeFactory(owner=owner)
        booking = BookingFactory(event_type=event_type, status="cancelled")
        api_client.force_authenticate(user=owner)
        response = api_client.get(f"/api/v1/bookings/{booking.id}/ical/")
        cal = Calendar.from_ical(response.content)
        vevent = next(c for c in cal.walk() if c.name == "VEVENT")
        assert vevent.get("status") == "CANCELLED"

    def test_confirmed_booking_has_confirmed_status(self, owner, api_client):
        event_type = EventTypeFactory(owner=owner)
        booking = BookingFactory(event_type=event_type)
        api_client.force_authenticate(user=owner)
        response = api_client.get(f"/api/v1/bookings/{booking.id}/ical/")
        cal = Calendar.from_ical(response.content)
        vevent = next(c for c in cal.walk() if c.name == "VEVENT")
        assert vevent.get("status") == "CONFIRMED"


@pytest.mark.django_db
class TestBookingIcalView:

    def test_ical_response_has_correct_content_type(self, owner, api_client):
        event_type = EventTypeFactory(owner=owner)
        booking = BookingFactory(event_type=event_type)
        api_client.force_authenticate(user=owner)
        response = api_client.get(f"/api/v1/bookings/{booking.id}/ical/")
        assert response.status_code == 200
        assert response.headers["Content-Type"].startswith("text/calendar")

    def test_ical_response_has_correct_content_disposition(self, owner, api_client):
        event_type = EventTypeFactory(owner=owner)
        booking = BookingFactory(event_type=event_type)
        api_client.force_authenticate(user=owner)
        response = api_client.get(f"/api/v1/bookings/{booking.id}/ical/")
        assert response.status_code == 200
        assert "attachment" in response.headers["Content-Disposition"]
        assert ".ics" in response.headers["Content-Disposition"]

    def test_unauthenticated_returns_401(self, api_client):
        booking = BookingFactory()
        response = api_client.get(f"/api/v1/bookings/{booking.id}/ical/")
        assert response.status_code == 401

    def test_non_owner_returns_403(self, owner, other_user, api_client):
        event_type = EventTypeFactory(owner=owner)
        booking = BookingFactory(event_type=event_type)
        api_client.force_authenticate(user=other_user)
        response = api_client.get(f"/api/v1/bookings/{booking.id}/ical/")
        assert response.status_code == 403

    def test_nonexistent_booking_returns_404(self, auth_client):
        response = auth_client.get(f"/api/v1/bookings/{uuid.uuid4()}/ical/")
        assert response.status_code == 404
