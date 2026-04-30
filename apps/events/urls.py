from rest_framework import routers
from apps.events.views import EventTypeViewSet

router = routers.DefaultRouter()
router.register(r'event-types', EventTypeViewSet, basename='event-type')
urlpatterns = router.urls