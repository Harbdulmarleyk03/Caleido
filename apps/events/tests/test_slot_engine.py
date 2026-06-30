import pytest
import pytz
from datetime import date, time, datetime
from apps.events.slot_engine import apply_date_override, get_availability_window


@pytest.fixture
def saturday_rules():
    return [{"day_of_week": 5, "start_time": time(9, 0), "end_time": time(17, 0)}]


def test_returns_utc_window_when_date_matches_rule(saturday_rules):
    owner_timezone = "Africa/Lagos"
    target_date = date(2026, 5, 9)

    window_start, window_end = get_availability_window(
        saturday_rules, target_date, owner_timezone
    )

    tz = pytz.timezone(owner_timezone)

    expected_start = tz.localize(datetime.combine(target_date, time(9, 0))).astimezone(
        pytz.UTC
    )
    expected_end = tz.localize(datetime.combine(target_date, time(17, 0))).astimezone(
        pytz.UTC
    )

    assert window_start == expected_start
    assert window_end == expected_end


def test_returns_utc_window_when_date_do_not_matches_rule(saturday_rules):
    owner_timezone = "Africa/Lagos"
    target_date = date(2026, 5, 7)

    window_start, window_end = get_availability_window(
        saturday_rules, target_date, owner_timezone
    )

    assert window_start is None
    assert window_end is None


def test_apply_date_override_with_unavailable():
    overrides = [{"specific_date": date(2026, 5, 9), "is_unavailable": True}]
    owner_timezone = "Africa/Lagos"
    target_date = date(2026, 5, 9)

    result = apply_date_override(overrides, target_date, owner_timezone)

    assert result == (None, None)


def test_apply_date_override_with_custom_times():
    overrides = [
        {
            "specific_date": date(2026, 5, 9),
            "is_unavailable": False,
            "custom_start": time(10, 0),
            "custom_end": time(15, 0),
        }
    ]
    owner_timezone = "Africa/Lagos"
    target_date = date(2026, 5, 9)

    result = apply_date_override(overrides, target_date, owner_timezone)

    tz = pytz.timezone(owner_timezone)
    expected_start = tz.localize(datetime.combine(target_date, time(10, 0))).astimezone(
        pytz.UTC
    )
    expected_end = tz.localize(datetime.combine(target_date, time(15, 0))).astimezone(
        pytz.UTC
    )

    assert result == (expected_start, expected_end)


def test_apply_date_override_with_no_match():
    overrides = [{"specific_date": date(2026, 5, 9), "is_unavailable": True}]
    target_date = date(2026, 5, 9)
    result = apply_date_override(overrides, target_date, "Africa/Lagos")
    assert result == (None, None)
