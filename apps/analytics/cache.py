def build_analytics_cache_key(owner_id, period):
    return f"analytics:{owner_id}:{period}"