# scheduling/cache_keys.py

def build_slot_cache_key(
    event_type_id: int,
    date: str,
    timezone: str,
) -> str:
    return f"slots:{event_type_id}:{date}:{timezone}"