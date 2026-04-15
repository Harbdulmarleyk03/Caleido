import pytest 
from apps.users.models import User
from django.contrib.auth import authenticate

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
        assert user.is_verified == False

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
        data = {
            'email': 'john@example.com',
            'password': 'Secure123',
        }

        response = api_client.post('/api/v1/auth/login/', data, format='json')

        assert response.status_code == 200
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_login_wrong_password(self, api_client):
        data = {
            'email': 'john@example.com',
            'password': 'Wrongpassword',
        }

        response = api_client.post('/api/v1/auth/login/', data, format='json')

        assert response.status_code == 401
        
    def test_login_unverified_user(self, api_client):
        data = {
            'email': 'john@example.com',
            'password': 'Wrongpassword',
        }
        user = authenticate(is_verified=False, **data)
        
        response = api_client.post('/api/v1/auth/login/', data, format='json')
        assert response.status_code == 403

    def test_login_nonexistent_email(self, api_client):
        data = {
            'email': 'john@example.ku',
            'password': 'Wrongpassword',
        }
        
        response = api_client.post('/api/v1/auth/login/', data, format='json')
        assert response.status_code == 401
