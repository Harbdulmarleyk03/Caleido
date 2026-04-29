import pytest 
from apps.users.tokens import generate_verification_token
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db 
class TestAuthE2EFlow:
    def test_user_auth_flow(self, api_client):
        register_response = api_client.post('/api/v1/auth/register/', {"email": "john@example.com",
                    "password": "Secure123", 'password2': 'Secure123', 'first_name': 'John',
            'last_name': 'Doe', 'username': 'johndoe', 'timezone': 'Africa/Lagos',})
        
        assert register_response.status_code == 201 
      
        user = User.objects.get(email="john@example.com", is_verified=False)
        token = generate_verification_token(user)

        verify_email_response = api_client.get('/api/v1/auth/verify-email/', {'token': str(token)})
        assert verify_email_response.status_code == 200 

        user = User.objects.get(email="john@example.com", is_verified=True)

        login_response = api_client.post('/api/v1/auth/login/', {"email": "john@example.com", "password": "Secure123"})

        assert login_response.status_code == 200
        access = login_response.data['access']
        refresh = login_response.data['refresh']
       
        token_refresh_response = api_client.post('/api/v1/auth/token/refresh/', {'refresh': str(refresh)})

        assert token_refresh_response.status_code == 200 

        api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {access}')
        logout_response = api_client.post('/api/v1/auth/logout/', {'refresh': str(refresh)})

        assert logout_response.status_code == 204 

        token_refresh_response = api_client.post('/api/v1/auth/token/refresh/', {'refresh': str(refresh)})

        assert token_refresh_response.status_code == 401