import pytest 
from apps.users.models import User
from django.contrib.auth import authenticate
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


    '''def test_refresh_success(self, api_client):
        token_data = {
            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzc2NDIwMDU2LCJpYXQiOjE3NzY0MTkxNTcsImp0aSI6ImVmNWIxNjQwMWQyNzRkOWJiYjMxNDk2NjU3MjAxNjlhIiwidXNlcl9pZCI6ImE4Zjk3NDgzLTY0YjctNGIzMy1iMGI3LWZlM2FkNDkxODliYiJ9.vOdyW7XkILQ6ipsw9lIRUhvdEu9mBh3q71-IYKFxwPo",
            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc3NzAyMzk1NiwiaWF0IjoxNzc2NDE5MTU2LCJqdGkiOiI5OGI2ZTNlN2VjMDU0NTZmYjY4MGFjZGVlMjU0ZTI0OSIsInVzZXJfaWQiOiJhOGY5NzQ4My02NGI3LTRiMzMtYjBiNy1mZTNhZDQ5MTg5YmIifQ.ssNxXRB8eDJhMB7e4fm-kZ0QvQ5XJpipAfcR9VcOkuk"
        }
        
        new_data = {
            "new_access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzc2NDIwNDMwLCJpYXQiOjE3NzY0MTk1MzAsImp0aSI6IjE0ZjdmMjkwODViZTRhOGQ4MjU1ODVhMWI5ZGM0N2IzIiwidXNlcl9pZCI6ImE4Zjk3NDgzLTY0YjctNGIzMy1iMGI3LWZlM2FkNDkxODliYiJ9.c27D0GliQsU7CFOzhVHgI2pVi0IBFhdF919uaiiCwig",
            "new_refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc3NzAyMzk1NiwiaWF0IjoxNzc2NDE5MTU2LCJqdGkiOiI5OGI2ZTNlN2VjMDU0NTZmYjY4MGFjZGVlMjU0ZTI0OSIsInVzZXJfaWQiOiJhOGY5NzQ4My02NGI3LTRiMzMtYjBiNy1mZTNhZDQ5MTg5YmIifQ.ssNxXRB8eDJhMB7e4fm-kZ0QvQ5XJpipAfcR9VcOkuk"
        }

        response = api_client.post('/api/v1/auth/token/refresh/', token_data, format='json')
        assert response.status_code == 200


    def test_refresh_invalid_token(self, api_client):
        token_data = {
            'access': 'UEGddbbgdkke7549u3hvdfhhdjkyryu',
            'refresh': 'dhy4yeyeyfryfri439934hfhfkkdlk'
        }

        response = api_client.post('/api/v1/auth/token/refresh/', token_data, format='json')
        assert response.status_code == 401

    def test_refresh_blacklisted_token(self, api_client):
        token_data = {
            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzc2NDIwMDU2LCJpYXQiOjE3NzY0MTkxNTcsImp0aSI6ImVmNWIxNjQwMWQyNzRkOWJiYjMxNDk2NjU3MjAxNjlhIiwidXNlcl9pZCI6ImE4Zjk3NDgzLTY0YjctNGIzMy1iMGI3LWZlM2FkNDkxODliYiJ9.vOdyW7XkILQ6ipsw9lIRUhvdEu9mBh3q71-IYKFxwPo",
            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc3NzAyMzk1NiwiaWF0IjoxNzc2NDE5MTU2LCJqdGkiOiI5OGI2ZTNlN2VjMDU0NTZmYjY4MGFjZGVlMjU0ZTI0OSIsInVzZXJfaWQiOiJhOGY5NzQ4My02NGI3LTRiMzMtYjBiNy1mZTNhZDQ5MTg5YmIifQ.ssNxXRB8eDJhMB7e4fm-kZ0QvQ5XJpipAfcR9VcOkuk"
        }

        new_data = {
            "new_access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzc2NDIwNDMwLCJpYXQiOjE3NzY0MTk1MzAsImp0aSI6IjE0ZjdmMjkwODViZTRhOGQ4MjU1ODVhMWI5ZGM0N2IzIiwidXNlcl9pZCI6ImE4Zjk3NDgzLTY0YjctNGIzMy1iMGI3LWZlM2FkNDkxODliYiJ9.c27D0GliQsU7CFOzhVHgI2pVi0IBFhdF919uaiiCwig",
            "new_refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc3NzAyMzk1NiwiaWF0IjoxNzc2NDE5MTU2LCJqdGkiOiI5OGI2ZTNlN2VjMDU0NTZmYjY4MGFjZGVlMjU0ZTI0OSIsInVzZXJfaWQiOiJhOGY5NzQ4My02NGI3LTRiMzMtYjBiNy1mZTNhZDQ5MTg5YmIifQ.ssNxXRB8eDJhMB7e4fm-kZ0QvQ5XJpipAfcR9VcOkuk"
        }
        response = api_client.post('/api/v1/auth/token/refresh/', token_data, format='json')
        assert response.status_code == 401 '''