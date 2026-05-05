from rest_framework import routers
from apps.events.views import EventTypeViewSet
from django.urls import path 
from apps.events import views 

router = routers.DefaultRouter()
router.register(r'event-types', EventTypeViewSet, basename='event-type')
urlpatterns = router.urls

urlpatterns += [
    path('event-types/<uuid:event_type_id>/availability/<uuid:pk>/', views.AvailabilityRuleDetailView.as_view(), name='availability-rule-detail'),
    path('event-types/<uuid:event_type_id>/availability/', views.AvailabilityRuleListCreateView.as_view(), name='availability-rule-list-create'),
    path('event-types/<uuid:event_type_id>/date-override/<uuid:pk>/', views.DateOverrideDetailView.as_view(), name='date-override-detail'),
    path('event-types/<uuid:event_type_id>/date-override/', views.DateOverrideListCreateView.as_view(), name='date-override-list-create'),
]