from django.urls import path
from apps.users import views

urlpatterns = [
    path('me/', views.UserProfileView.as_view(), name='user-profile'),
]