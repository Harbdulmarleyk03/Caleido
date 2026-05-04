import pytest
from apps.users.tests.factories import UserFactory
from apps.events.models import AvailabilityRule, EventType
from django.urls import reverse

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
        slug="my-first-event-type")

def availability_rule(event_type):
    return AvailabilityRule.objects.create(
            event_type=event_type,
            day_of_week=3,
            start_time=9,
            end_time=12)

@pytest.fixture
def auth_client(api_client, owner):
    api_client.force_authenticate(user=owner)
    return api_client

@pytest.mark.django_db
class TestAvailabilityRuleView:

    def test_list_authenticated_user(self, auth_client):
        url = reverse('availability-rule-list-create')
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_list_unauthenticated_user(self, api_client):
        url = reverse('availability-rule-list-create')
        response = api_client.get(url)
        assert response.status_code == 401

    def test_list_only_shows_own_event_types(self, auth_client, event_type, other_user):
        EventType.objects.create(
            owner=other_user,
            title="Other user's event type",
            duration_minutes=30,
            location_type='zoom',
            slug="other-event-type",
        )
        url = reverse('event-type-list')
        response = auth_client.get(url)
        assert response.status_code == 200
        # Only the owner's event type should appear
        assert len(response.data) == 1
        assert response.data[0]['title'] == "My first event type"
    
    def test_create_rule(self, auth_client, owner):
        url = reverse('availability-rule-list-create')
        data = {
            "event_type": "AI trends",
            "day_of_week": 2,
            "start_time": "9:00:00",
            "end_time": "12:00:00",
        }
        response = auth_client.post(url, data)
        assert response.status_code == 201

    def test_create_rule_overlap(self, auth_client, owner):
        AvailabilityRule.objects.create(
            owner=owner,
            event_type="AI trends",
            day_of_week=2,
            start_time="9:00:00",
            end_time="12:00:00",
        )
        url = reverse('availability-rule-list-create')
        data = {
            "event_type": "AI trends",
            "day_of_week": 2,
            "start_time": "11:00:00",
            "end_time": "13:00:00",
        }
        response = auth_client.post(url, data)
        assert response.status_code == 400
        assert 'overlaps with an existing rule' in str(response.data)

    def test_create_rule_invalid_time(self, auth_client):
        url = reverse('availability-rule-list-create')
        AvailabilityRule.objects.create(
            owner=owner,
            event_type="AI trends",
            day_of_week=2,
            start_time="13:00:00",
            end_time="12:00:00",
        )
        response = auth_client.post(url)
        assert response.status_code == 400 

    def test_update_rule(self, auth_client, availability_rule):
        url = reverse('availability-rule-detail')
        data = {
            "event_type": "AI trends",
            "day_of_week": 2,
            "start_time": "11:00:00",
            "end_time": "13:00:00",
        }
        response = auth_client.patch(url, data)
        assert response.status_code == 200
        availability_rule.refresh_from_db()
        assert availability_rule.start_time == "12:00:00"
    
    def test_retrieve_rule(self, auth_client, availability_rule):
        url = reverse('availability-rule-detail')
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.data['end_time'] == availability_rule.end_time

    def test_delete_rule(self, auth_client, availability_rule):
        url = reverse('availability-rule-detail')
        response = auth_client.delete(url)
        assert response.status_code == 204

    def test_non_owner_cannot_retrieve(self, api_client, other_user):
        api_client.force_authenticate(user=other_user)
        url = reverse('availability-rule-detail')
        response = api_client.get(url)
        assert response.status_code == 403
 

    def test_non_owner_cannot_update(self, api_client, other_user, availability_rule):
        api_client.force_authenticate(user=other_user)
        url = reverse('availability-rule-detail')
        response = api_client.patch(url, {'start_time': '11:00:00'})
        assert response.status_code == 403
        availability_rule.refresh_from_db()
        assert availability_rule.start_time == "12:30:00"
 

    def test_non_owner_cannot_delete(self, api_client, other_user):
        api_client.force_authenticate(user=other_user)
        url = reverse('availability-rule-detail')
        response = api_client.delete(url)
        assert response.status_code == 403
 