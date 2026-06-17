import pytest
from django.core.cache import cache
from django.urls import reverse
from unittest.mock import patch
from apps.analytics.services import AnalyticService
from apps.analytics.cache import build_analytics_cache_key, PERIODS
from apps.bookings.tests.factories import BookingFactory
from apps.events.tests.factories import EventTypeFactory
from apps.users.tests.factories import UserFactory


@pytest.mark.django_db
class TestAnalyticsService:

    def test_cache_miss_computes_and_stores(self):
        booking = BookingFactory()
        owner = booking.event_type.owner
        period = "all"
        key = build_analytics_cache_key(owner_id=owner.id, period=period)

        assert cache.get(key) is None

        result = AnalyticService.get_owner_analytics(owner=owner, period=period)

        assert result["total_bookings"] == 1
        assert cache.get(key) == result

    def test_cache_hit_skips_db(self):
        booking = BookingFactory()
        owner = booking.event_type.owner
        period = "all"
        key = build_analytics_cache_key(owner_id=owner.id, period=period)

        fake = {"total_bookings": 99, "cached": True}
        cache.set(key, fake)

        with patch("apps.analytics.services.Booking.objects") as mock_qs:
            result = AnalyticService.get_owner_analytics(owner=owner, period=period)

        # DB never touched
        mock_qs.filter.assert_not_called()
        assert result == fake

    def test_zero_bookings_no_division_error(self):
        owner = UserFactory()
        result = AnalyticService.get_owner_analytics(owner=owner, period="all")

        assert result["total_bookings"] == 0
        assert result["cancellation_rate"] == 0
        assert result["average_lead_time"] is None

    def test_cancellation_rate_computed_correctly(self):
        event_type = EventTypeFactory()
        owner = event_type.owner
        BookingFactory(event_type=event_type, status="confirmed")
        BookingFactory(event_type=event_type, status="confirmed")
        BookingFactory(event_type=event_type, status="cancelled")

        result = AnalyticService.get_owner_analytics(owner=owner, period="all")

        assert result["total_bookings"] == 3
        assert result["cancellation_rate"] == pytest.approx(33.33, rel=1e-2)

    def test_period_filter_excludes_old_bookings(self):
        from datetime import timedelta
        from django.utils import timezone as tz

        event_type = EventTypeFactory()
        owner = event_type.owner

        # Recent booking — within 7d window
        BookingFactory(event_type=event_type)

        # Old booking — outside 7d window; override created_at directly
        old_booking = BookingFactory(event_type=event_type)
        old_booking.created_at = tz.now() - timedelta(days=30)
        old_booking.save(update_fields=["created_at"])

        result = AnalyticService.get_owner_analytics(owner=owner, period="7d")

        assert result["total_bookings"] == 1

    def test_owner_sees_only_own_bookings(self):
        owner_a = UserFactory()
        owner_b = UserFactory()
        event_type_a = EventTypeFactory(owner=owner_a)
        event_type_b = EventTypeFactory(owner=owner_b)
        BookingFactory(event_type=event_type_a)
        BookingFactory(event_type=event_type_b)

        result = AnalyticService.get_owner_analytics(owner=owner_a, period="all")

        assert result["total_bookings"] == 1


@pytest.mark.django_db(transaction=True)
class TestAnalyticsSignal:

    def test_booking_create_invalidates_all_periods(self):
        event_type = EventTypeFactory()
        owner = event_type.owner

        # Prime all period keys
        for period in PERIODS:
            key = build_analytics_cache_key(owner_id=owner.id, period=period)
            cache.set(key, {"total_bookings": 0})

        BookingFactory(event_type=event_type)

        for period in PERIODS:
            key = build_analytics_cache_key(owner_id=owner.id, period=period)
            assert cache.get(key) is None, f"Expected key for period '{period}' to be invalidated"

    def test_booking_delete_invalidates_all_periods(self):
        booking = BookingFactory()
        owner = booking.event_type.owner

        for period in PERIODS:
            key = build_analytics_cache_key(owner_id=owner.id, period=period)
            cache.set(key, {"total_bookings": 1})

        booking.delete()

        for period in PERIODS:
            key = build_analytics_cache_key(owner_id=owner.id, period=period)
            assert cache.get(key) is None, f"Expected key for period '{period}' to be invalidated"

    def test_signal_only_invalidates_affected_owner(self):
        owner_a = UserFactory()
        owner_b = UserFactory()
        event_type_a = EventTypeFactory(owner=owner_a)
        EventTypeFactory(owner=owner_b)

        key_b = build_analytics_cache_key(owner_id=owner_b.id, period="all")
        cache.set(key_b, {"total_bookings": 5})

        # Booking for owner_a fires the signal
        BookingFactory(event_type=event_type_a)

        # owner_b's cache must be untouched
        assert cache.get(key_b) == {"total_bookings": 5}

@pytest.mark.django_db
class TestAnalyticsView:

    def test_unauthenticated_returns_401(self, client):
        url = reverse("analytics")
        response = client.get(url)
        assert response.status_code == 401

    def test_invalid_period_returns_400(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        url = reverse("analytics")
        response = api_client.get(url, {"period": "invalid"})
        assert response.status_code == 400
        assert "period" in response.data["details"]

    def test_valid_period_returns_200(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        url = reverse("analytics")
        response = api_client.get(url, {"period": "30d"})
        assert response.status_code == 200
        assert "total_bookings" in response.data

    def test_default_period_is_all(self, api_client):
        user = UserFactory()
        api_client.force_authenticate(user=user)
        url = reverse("analytics")
        response = api_client.get(url)
        assert response.status_code == 200

    def test_view_uses_request_user_not_query_param(self, api_client):
        owner_a = UserFactory()
        owner_b = UserFactory()
        event_type = EventTypeFactory(owner=owner_a)
        BookingFactory(event_type=event_type)

        api_client.force_authenticate(user=owner_b)
        url = reverse("analytics")
        response = api_client.get(url, {"period": "all", "owner_id": str(owner_a.id)})

        assert response.status_code == 200
        assert response.data["total_bookings"] == 0