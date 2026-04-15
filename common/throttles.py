from rest_framework.throttling import AnonRateThrottle

class AuthRateThrottle(AnonRateThrottle):
    scope = 'auth'

class AnonSlotThrottle(AnonRateThrottle):
    scope = 'anon_slot'
