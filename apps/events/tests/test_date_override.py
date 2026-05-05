import pytest
from apps.users.tests.factories import UserFactory
from apps.events.models import DateOverride, EventType
from django.urls import reverse

@pytest.fixture
def other_user(db):
    return UserFactory(is_verified=True)

@pytest.fixture
def event_type(owner):
    return EventType.objects.create(
        owner=owner,
        title="My first event type",
        description="This is my first description",
        duration_minutes=30,
        location_type='zoom',
        buffer_before_min=5,
        buffer_after_min=5,
        min_notice_hours=1,
        max_future_days=1,
        slug="my-first-event-type")

@pytest.fixture
def date_override(event_type):
    return DateOverride.objects.create(
            event_type=event_type,
            specific_date="2024-12-25",
            custom_start="9:00:00",
            custom_end="12:00:00")

@pytest.fixture
def auth_client(api_client, owner):
    api_client.force_authenticate(user=owner)
    return api_client

@pytest.mark.django_db
class TestDateOverrideView:

    def test_list_authenticated_user(self, auth_client, event_type):
        url = reverse('date-override-list-create', kwargs={'event_type_id': event_type.pk})
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_list_unauthenticated_user(self, api_client, event_type):
        url = reverse('date-override-list-create', kwargs={'event_type_id': event_type.pk})
        response = api_client.get(url)
        assert response.status_code == 401
    
    def test_create_rule(self, auth_client, owner, event_type):
        url = reverse('date-override-list-create', kwargs={'event_type_id': event_type.pk})
        data = {
            "specific_date": "2024-12-25",
            "custom_start": "9:00:00",
            "custom_end": "12:00:00",
        }
        response = auth_client.post(url, data)
        assert response.status_code == 201

    def test_create_rule_overlap(self, auth_client, event_type, owner):
        DateOverride.objects.create(
            event_type=event_type,
            specific_date="2024-12-25",
            custom_start="9:00:00",
            custom_end="12:00:00",
        )
        url = reverse('date-override-list-create', kwargs={'event_type_id': event_type.pk})
        data = {
            "specific_date": "2024-12-25",
            "custom_start": "11:00:00",
            "custom_end": "13:00:00",
        }
        response = auth_client.post(url, data)
        assert response.status_code == 400
        assert 'overlaps with an existing rule' in str(response.data)

    def test_create_rule_invalid_time(self, auth_client, event_type):
        url = reverse('date-override-list-create', kwargs={'event_type_id': event_type.pk})
        DateOverride.objects.create(
            event_type=event_type,
            specific_date="2024-12-25",
            custom_start="9:00:00",
            custom_end="12:00:00",
        )
        url = reverse('date-override-list-create', kwargs={'event_type_id': event_type.pk})
        data = {
            "specific_date": "2024-12-25",
            "custom_start": "13:00:00",
            "custom_end": "12:00:00",
        }
        response = auth_client.post(url, data)
        assert response.status_code == 400 
    
    def test_retrieve_rule(self, auth_client, date_override, event_type):
        url = reverse('date-override-detail', kwargs={'event_type_id': event_type.pk, 'pk': date_override.pk})
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.data['custom_end'] == date_override.custom_end

    def test_delete_rule(self, auth_client, date_override, event_type):
        url = reverse('date-override-detail', kwargs={'event_type_id': event_type.pk, 'pk': date_override.pk})
        response = auth_client.delete(url)
        assert response.status_code == 204

    def test_non_owner_cannot_retrieve(self, api_client, other_user, date_override, event_type):
        api_client.force_authenticate(user=other_user)
        url = reverse('date-override-detail', kwargs={'event_type_id': event_type.pk, 'pk': date_override.pk})
        response = api_client.get(url)
        assert response.status_code == 404

    def test_non_owner_cannot_delete(self, api_client, other_user, date_override, event_type):
        api_client.force_authenticate(user=other_user)
        url = reverse('date-override-detail', kwargs={'event_type_id': event_type.pk, 'pk': date_override.pk})
        response = api_client.delete(url)
        assert response.status_code == 404
 