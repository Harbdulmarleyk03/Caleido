from django.urls import path
from apps.health import views

urlpatterns = [
    path('', views.HealthAPIView.as_view(), name='health'),
]


