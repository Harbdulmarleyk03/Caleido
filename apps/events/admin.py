from django.contrib import admin
from apps.events.models import EventType, AvailabilityRule, DateOverride, EventTypeQuestion

@admin.register(EventType)
class EventTypeAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ("title",)}

admin.site.register(AvailabilityRule)
admin.site.register(DateOverride)
admin.site.register(EventTypeQuestion)