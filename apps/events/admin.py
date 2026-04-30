from django.contrib import admin
from apps.events.models import EventType, AvailabilityRule, DateOverride, EventTypeQuestion

admin.site.register(EventType)
admin.site.register(AvailabilityRule)
admin.site.register(DateOverride)
admin.site.register(EventTypeQuestion)