import pytest
from django.urls import reverse
from rest_framework import status
from apps.users.tests.factories import UserFactory
from apps.events.models import EventType

@pytest.fixture
def owner(db):
    return UserFactory(is_verified=True)

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
        slug="my-first-event-type",
    )

@pytest.fixture
def auth_client(api_client, owner):
    api_client.force_authenticate(user=owner)
    return api_client


@pytest.mark.django_db
class TestEventTypeViewSet:

    def test_list_authenticated_user(self, auth_client, event_type, owner):
        url = reverse('event-type-list')
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        returned_ids = [item['id'] for item in response.data]
        assert str(event_type.id) in returned_ids

    def test_list_unauthenticated_user(self, api_client):
        url = reverse('event-type-list')
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_only_shows_own_event_types(self, auth_client, event_type, other_user):
        # Create an event type for a different user
        EventType.objects.create(
            owner=other_user,
            title="Other user's event type",
            duration_minutes=30,
            location_type='zoom',
            slug="other-event-type",
        )
        url = reverse('event-type-list')
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        # Only the owner's event type should appear
        assert len(response.data) == 1
        assert response.data[0]['title'] == "My first event type"

    def test_create_event_type(self, auth_client, owner):
        url = reverse('event-type-list')
        data = {
            'title': 'The obedient man',
            'duration_minutes': 30,
            'location_type': 'zoom',
            'buffer_before_min': 5,
            'buffer_after_min': 5,
            'min_notice_hours': 1,
            'max_future_days': 1,
        }
        response = auth_client.post(url, data)
        assert response.status_code == status.HTTP_201_CREATED
        # Verify it was actually saved to the DB
        event_type = EventType.objects.get(title="The obedient man")
        assert event_type.owner == owner
        # Verify slug was auto-generated
        assert event_type.slug == 'the-obedient-man'

    def test_create_unauthenticated(self, api_client):
        url = reverse('event-type-list')
        response = api_client.post(url, {'title': 'test'})
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_retrieve_event_type(self, auth_client, event_type):
        url = reverse('event-type-detail', args=[event_type.pk])
        response = auth_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert response.data['title'] == event_type.title

    def test_update_event_type(self, auth_client, event_type):
        url = reverse('event-type-detail', args=[event_type.pk])
        data = {'title': 'Updated title'}
        response = auth_client.patch(url, data)
        assert response.status_code == status.HTTP_200_OK
        event_type.refresh_from_db()
        assert event_type.title == 'Updated title'

    def test_delete_event_type(self, auth_client, event_type):
        url = reverse('event-type-detail', args=[event_type.pk])
        response = auth_client.delete(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not EventType.objects.filter(pk=event_type.pk).exists()

    def test_non_owner_cannot_update(self, api_client, other_user, event_type):
        api_client.force_authenticate(user=other_user)
        url = reverse('event-type-detail', args=[event_type.pk])
        response = api_client.patch(url, {'title': 'Hacked'})
        assert response.status_code == status.HTTP_403_FORBIDDEN
        # Verify the title was NOT changed in the DB
        event_type.refresh_from_db()
        assert event_type.title == "My first event type"

    def test_non_owner_cannot_delete(self, api_client, other_user, event_type):
        api_client.force_authenticate(user=other_user)
        url = reverse('event-type-detail', args=[event_type.pk])
        response = api_client.delete(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN
        # Verify the record still exists
        assert EventType.objects.filter(pk=event_type.pk).exists()

    def test_filter_by_is_active(self, auth_client, owner, event_type):
        # Create an inactive event type
        EventType.objects.create(
            owner=owner,
            title="Inactive event type",
            duration_minutes=30,
            location_type='zoom',
            slug="inactive-event-type",
            is_active=False,
        )
        url = reverse('event-type-list')
        # Filter active only
        response = auth_client.get(url, {'is_active': 'true'})
        assert response.status_code == status.HTTP_200_OK
        assert all(item['is_active'] for item in response.data)
        # Filter inactive only
        response = auth_client.get(url, {'is_active': 'false'})
        assert response.status_code == status.HTTP_200_OK
        assert all(not item['is_active'] for item in response.data)