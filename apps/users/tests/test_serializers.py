import pytest 
from apps.users.serializers import RegisterSerializer
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
class TestRegisterSerializer:

    def test_valid_data_passes(self):
        data = {
            'email': 'test@example.com',
            'password': 'Secure123',
            'password2': 'Secure123',
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'johndoe',
            'timezone': 'Africa/Lagos',
        }
        serializer = RegisterSerializer(data=data)
        assert serializer.is_valid(), serializer.errors

    def test_weak_password_rejected(self):
        data = {
            'email': 'test@example.com',
            'password': "alllowercase1",
            'password2': "alllowercase1",
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'johndoe',
            'timezone': 'Africa/Lagos',
        }     
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors

    def test_no_number_password_rejected(self):
        data = {
            'email': 'test@example.com',
            'password': "NoNumbers",
            'password2': "NoNumbers",
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'johndoe',
            'timezone': 'Africa/Lagos',
        } 
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert 'password' in serializer.errors

    def test_non_matched_password_rejected(self):
        data = {
            'email': 'test@example.com',
            'password': "Secure123",
            'password2': "Secure456",
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'johndoe',
            'timezone': 'Africa/Lagos',
        } 
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert 'non_field_errors' in serializer.errors

   
    def test_duplicate_email_rejected(self):
        User.objects.create_user(
            email='taken@example.com',
            password='Secure123',
            first_name='Jane',
            last_name='Doe',
            username='janedoe',
        )
        data = {
            'email': 'taken@example.com', 
            'password': 'Secure123',
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'johndoe',
            'timezone': 'Africa/Lagos',
        }
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert 'email' in serializer.errors


    
    def test_duplicate_username_rejected(self):
        User.objects.create_user(
            email='test@example.com',
            password='Secure123',
            first_name='Jane',
            last_name='Doe',
            username='janedoe',
        )
        data = {
            'email': 'taken@example.com',  
            'password': 'Secure123',
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'janedoe',
            'timezone': 'Africa/Lagos',
        }
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert 'username' in serializer.errors

    def test_invalid_timezone_rejected(self):
        data = {
            'email': 'taken@example.com',  
            'password': 'Secure123',
            'first_name': 'John',
            'last_name': 'Doe',
            'username': 'johndoe',
            'timezone': 'Lagos',
        }
        serializer = RegisterSerializer(data=data)
        assert not serializer.is_valid()
        assert 'timezone' in serializer.errors
        