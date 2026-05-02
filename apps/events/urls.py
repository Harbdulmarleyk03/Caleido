from rest_framework import routers
from apps.events.views import EventTypeViewSet
from django.urls import path 
from apps.events import views 

router = routers.DefaultRouter()
router.register(r'event-types', EventTypeViewSet, basename='event-type')
urlpatterns = router.urls

urlpatterns += [
    path('availability/<int:id>/', views.AvailabilityScheduleDetailView.as_view()),
    path('availability/', views.AvailabilityScheduleListView.as_view())
]