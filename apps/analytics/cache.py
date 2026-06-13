from datetime import timedelta
from django.utils import timezone

PERIOD_DAYS = {
        "7d": 7,
        "30d": 30,
        "90d": 90,
    }

PERIODS = list(PERIOD_DAYS.keys()) + ["all"]

def get_period_cutoff(period):
    days = PERIOD_DAYS.get(period)
    if days is None:
        return None  # "all" or unrecognised → no lower bound
    return timezone.now() - timedelta(days=days)

def build_analytics_cache_key(owner_id, period):    
    period = period if period in PERIOD_DAYS else "all"
    return f"analytics:{owner_id}:{period}"