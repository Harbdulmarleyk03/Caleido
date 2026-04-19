import pytest 
from apps.users.models import OutstandingToken, User
from rest_framework_simplejwt.tokens import RefreshToken
from apps.users.tests.factories import UserFactory

@pytest.mark.django_db
class TestRegisterView:
    
    def test_register_success(self, api_client):
        data = {
            'email': 'john@example.com',
            'password': 'Secure123',
            'password2': 'Secure123',
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'johndoe',
            'timezone': 'Africa/Lagos',
        }
        response = api_client.post('/api/v1/auth/register/', data, format='json')
        
        assert response.status_code == 201
        assert User.objects.filter(email='john@example.com').exists()
        user = User.objects.get(email='john@example.com')
        assert user.check_password('Secure123')  # confirms password was hashed
        assert user.is_verified == True

    def test_register_duplicate_email(self, api_client):
        User.objects.create_user(
            email='john@example.com',
            password='Secure123',
            first_name='John',
            last_name='Doe',
            username='johndoe',
        )
        data = {
            'email': 'john@example.com',
            'password': 'Secure123',
            'password2': 'Secure123',
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'johndoe2',  # different username to isolate the email conflict
            'timezone': 'Africa/Lagos',
        }
        response = api_client.post('/api/v1/auth/register/', data, format='json')
        assert response.status_code == 400
        assert 'email' in response.data

    def test_register_missing_fields(self, api_client):
        data = {
                'password': 'Secure123',
                'password2': 'Secure123',
                'username': 'johndoe',
                'first_name': 'John',
                'last_name': 'Doe',
                'timezone': 'Africa/Lagos',
            }

        response = api_client.post('/api/v1/auth/register/', data, format='json')
        assert response.status_code == 400
        assert "email" in response.data

    def test_register_weak_password(self, api_client):
        data = {
                'email': 'john@example.com',
                'password': 'weakpass',
                'password2': 'weakpass',
                'first_name': 'John',
                'last_name': 'Doe',
                'username': 'johndoe',
                'timezone': 'Africa/Lagos',
            }

        response = api_client.post('/api/v1/auth/register/', data, format='json')
        assert response.status_code == 400

@pytest.mark.django_db
class TestLoginView:

    def test_login_success(self, api_client):
        user = User.objects.create_user(
            username='johndoe',
            email="john@example.com",
            password="Secure123",
            is_verified=True
        )
        data = {
            'username': 'johndoe',
            "email": "john@example.com",
            "password": "Secure123",
        }
        response = api_client.post("/api/v1/auth/login/", data, format="json")

        assert response.status_code == 200
        assert "access" in response.data
        assert "refresh" in response.data

    def test_login_wrong_password(self, api_client):
        User.objects.create_user(
            username='johndoe',
            email="john@example.com",
            password="Secure123",
            is_verified=True
        )
        data = {
            'username': 'johndoe',
            "email": "john@example.com",
            "password": "Wrongpassword",
        }
        response = api_client.post("/api/v1/auth/login/", data, format="json")
        assert response.status_code == 401

    def test_login_unverified_user(self, api_client):
        User.objects.create_user(
            username= 'johndoe',
            email="john@example.com",
            password="Secure123",
            is_verified=False
        )
        data = {
            'username': 'johndoe',
            "email": "john@example.com",
            "password": "Secure123",
        }
        response = api_client.post("/api/v1/auth/login/", data, format="json")
        assert response.status_code == 403

    def test_login_nonexistent_email(self, api_client):
        data = {
            "email": "doesnotexist@example.com",
            "password": "Secure123",
        }
        response = api_client.post("/api/v1/auth/login/", data, format="json")
        assert response.status_code == 401

@pytest.mark.django_db
class TestTokenRefreshView:

    def test_refresh_success(self, api_client):
        user = UserFactory(is_verified=True)
        refresh = RefreshToken.for_user(user)
        
        response = api_client.post('/api/v1/auth/token/refresh/', {'refresh': str(refresh)}, format='json')
        
        assert response.status_code == 200
        assert 'new_access' in response.data
        assert 'new_refresh' in response.data

    def test_refresh_invalid_token(self, api_client):
        response = api_client.post('/api/v1/auth/token/refresh/', {'refresh': 'thisisnot.avalid.token'}, format='json')
        
        assert response.status_code == 401

    def test_refresh_blacklisted_token(self, api_client):
        user = UserFactory(is_verified=True)
        refresh = RefreshToken.for_user(user)
        
        # First request — valid, blacklists the token
        api_client.post('/api/v1/auth/token/refresh/', {'refresh': str(refresh)}, format='json')
        
        # Second request — same token, now blacklisted
        response = api_client.post('/api/v1/auth/token/refresh/', {'refresh': str(refresh)}, format='json')
        
        assert response.status_code == 401

@pytest.mark.django_db(transaction=True)
class TestLogoutView:

    def test_logout_success(self, api_client):
        user = UserFactory(is_verified=True)
        refresh = RefreshToken.for_user(user)
        api_client.force_authenticate(user=user)
        response = api_client.post('/api/v1/auth/logout/', {'refresh': str(refresh)}, format='json')

        assert response.status_code == 204 

    def test_logout_unauthenticated(self, api_client):

        response = api_client.post('/api/v1/auth/logout/', format='json')
        assert response.status_code == 401 

    def test_logout_invalid_token(self, api_client):
        user = UserFactory(is_verified=True)
        refresh = 'Not.a.valid.token'
        
        api_client.force_authenticate(user=user)

        response = api_client.post('/api/v1/auth/logout/', {'refresh': str(refresh)}, format='json')
        assert response.status_code == 400 
        
    def test_logout_all_blacklist_all_tokens(self, api_client):
        user = User.objects.create_user(
            username='johndoe',
            email="john@example.com",
            password="Secure123",
            is_verified=True
        )
        from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
        
        refresh1 = RefreshToken.for_user(user)
        refresh2 = RefreshToken.for_user(user)
        
        # Directly blacklist all tokens for user
        tokens = OutstandingToken.objects.filter(user=user)
        for token in tokens:
            BlacklistedToken.objects.get_or_create(token=token)
        
        # Verify tokens are blacklisted
        assert BlacklistedToken.objects.count() == 2
        
        # Try to use old refresh token via API
        api_client.credentials()
        response = api_client.post(
            '/api/v1/auth/token/refresh/', 
            {'refresh': str(refresh1)}, 
            format='json'
        )
        assert response.status_code == 401
        
    def test_logout_all_success(self, api_client):

        user = User.objects.create_user(
                username= 'johndoe',
                email="john@example.com",
                password="Secure123",
                is_verified=True
            )

        tokens = OutstandingToken.objects.filter(user=user)
        refresh = RefreshToken.for_user(user)
        api_client.force_authenticate(user=user)

        response = api_client.post('/api/v1/auth/logout-all/', {'tokens': str(tokens), 'refresh': str(refresh)}, format='json')

        assert response.status_code == 204
