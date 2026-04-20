from django.urls import path
from apps.users import views

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('token/refresh/', views.TokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('logout-all/', views.LogoutAllView.as_view(), name='logout-all'),
    path('verify-email/', views.VerifyEmailView.as_view(), name='verify-email'),
    path('verify-email/resend/', views.ResendVerificationEmailView.as_view(), name='verify-email-resend'),
]
