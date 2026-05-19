from django.contrib import admin
from apps.bookings.models import Booking, BookingAnswer, BookingAudit, Invitee

# Register your models here.
admin.site.register(Booking)
admin.site.register(BookingAudit)
admin.site.register(BookingAnswer)
admin.site.register(Invitee)