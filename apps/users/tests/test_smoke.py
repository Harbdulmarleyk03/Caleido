import pytest
from django.contrib.auth import get_user_model

User = get_user_model()

@pytest.mark.django_db
def test_user_model_exists():
    user = User.objects.create_user(
        email="test@example.com",
        username="testuser",
        password="TestPass123!",
        first_name="Test",
        last_name="User",
    )
    assert user.id is not None         
    assert str(user) == "test@example.com"
    assert user.is_verified is False    

@pytest.mark.django_db
def test_user_profile(api_client):
    response = api_client.get('/api/v1/users/me/')
    assert response.status_code == 401 