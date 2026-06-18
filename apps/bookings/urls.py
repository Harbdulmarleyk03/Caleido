from rest_framework.routers import DefaultRouter
from apps.bookings.views import BookingViewSet, BookingIcalView
from django.urls import path

router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')
urlpatterns = router.urls

urlpatterns += [
    path('bookings/<uuid:booking_id>/ical/', BookingIcalView.as_view(), name='booking-ical'),
]