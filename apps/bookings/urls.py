from rest_framework.routers import DefaultRouter
from apps.bookings.views import BookingViewSet

router = DefaultRouter()
router.register(r'bookings', BookingViewSet, basename='booking')
urlpatterns = router.urls