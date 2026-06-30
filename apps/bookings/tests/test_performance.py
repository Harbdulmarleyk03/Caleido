import pytest
from django.utils import timezone as tz
from datetime import timedelta
from apps.events.tests.factories import EventTypeFactory, AvailabilityRuleFactory
from apps.bookings.tests.factories import BookingFactory


@pytest.mark.django_db
def test_slot_list_view_query_count(owner, django_assert_num_queries, api_client):
    event_type = EventTypeFactory(owner=owner)
    AvailabilityRuleFactory(event_type=event_type)
    date = (tz.now() + timedelta(days=1)).date().isoformat()

    with django_assert_num_queries(3):  # was 4
        api_client.get(
            f"/api/v1/events/event-types/{event_type.id}/slots/"
            f"?date={date}&timezone=UTC"
        )


@pytest.mark.django_db
def test_booking_ical_view_query_count(owner, django_assert_num_queries, api_client):
    event_type = EventTypeFactory(owner=owner)
    booking = BookingFactory(event_type=event_type)
    api_client.force_authenticate(user=owner)

    with django_assert_num_queries(1):  # was 2 — force_authenticate skips auth query
        api_client.get(f"/api/v1/bookings/{booking.id}/ical/")


@pytest.mark.django_db
def test_booking_list_query_count_constant(
    owner, django_assert_num_queries, api_client
):
    BookingFactory.create_batch(5, event_type=EventTypeFactory(owner=owner))
    api_client.force_authenticate(user=owner)

    with django_assert_num_queries(1):  # was 2 — one SELECT with JOIN, no N+1
        api_client.get("/api/v1/bookings/")
