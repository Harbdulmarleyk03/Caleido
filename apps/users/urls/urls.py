from django.urls import path
from apps.users import views

urlpatterns = [
    path('me/', views.UserProfileView.as_view(), name='user-profile'),
    path('me/password/', views.ChangePasswordView.as_view(), name='change-password'),
]