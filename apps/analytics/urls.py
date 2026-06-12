from django.urls import path
from . import views

urlpatterns = [
    path('analytics/', views.AnalyticsAPIView.as_view(), name='analytics'),
]