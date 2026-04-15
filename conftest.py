import pytest 
from rest_framework.test import APIClient
from apps.users.tests.factories import UserFactory 

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def user():
    return UserFactory()

@pytest.fixture
def verified_user():
    return UserFactory(is_verified=True)

@pytest.fixture
def auth_client(verified_user):
    client = APIClient()
    client.force_authenticate(user=verified_user)
    return client