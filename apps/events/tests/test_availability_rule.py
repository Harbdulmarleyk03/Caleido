import pytest
from apps.users.tests.factories import UserFactory
from apps.events.models import AvailabilityRule, EventType
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
        location_type="zoom",
        buffer_before_min=5,
        buffer_after_min=5,
        min_notice_hours=1,
        max_future_days=1,
        slug="my-first-event-type",
    )


@pytest.fixture
def availability_rule(event_type):
    return AvailabilityRule.objects.create(
        event_type=event_type, day_of_week=3, start_time="9:00:00", end_time="12:00:00"
    )


@pytest.fixture
def auth_client(api_client, owner):
    api_client.force_authenticate(user=owner)
    return api_client


@pytest.mark.django_db
class TestAvailabilityRuleView:

    def test_list_authenticated_user(self, auth_client, event_type):
        url = reverse(
            "availability-rule-list-create", kwargs={"event_type_id": event_type.pk}
        )
        response = auth_client.get(url)
        assert response.status_code == 200

    def test_list_unauthenticated_user(self, api_client, event_type):
        url = reverse(
            "availability-rule-list-create", kwargs={"event_type_id": event_type.pk}
        )
        response = api_client.get(url)
        assert response.status_code == 401

    def test_create_rule(self, auth_client, owner, event_type):
        url = reverse(
            "availability-rule-list-create", kwargs={"event_type_id": event_type.pk}
        )
        data = {
            "day_of_week": 2,
            "start_time": "9:00:00",
            "end_time": "12:00:00",
        }
        response = auth_client.post(url, data)
        assert response.status_code == 201

    def test_create_rule_overlap(self, auth_client, event_type, owner):
        AvailabilityRule.objects.create(
            event_type=event_type,
            day_of_week=2,
            start_time="9:00:00",
            end_time="12:00:00",
        )
        url = reverse(
            "availability-rule-list-create", kwargs={"event_type_id": event_type.pk}
        )
        data = {
            "day_of_week": 2,
            "start_time": "11:00:00",
            "end_time": "13:00:00",
        }
        response = auth_client.post(url, data)
        assert response.status_code == 400
        assert "overlaps with an existing rule" in str(response.data)

    def test_create_rule_invalid_time(self, auth_client, event_type):
        url = reverse(
            "availability-rule-list-create", kwargs={"event_type_id": event_type.pk}
        )
        AvailabilityRule.objects.create(
            event_type=event_type,
            day_of_week=2,
            end_time="12:00:00",
            start_time="13:00:00",
        )
        response = auth_client.post(url)
        assert response.status_code == 400

    def test_retrieve_rule(self, auth_client, availability_rule, event_type):
        url = reverse(
            "availability-rule-detail",
            kwargs={"event_type_id": event_type.pk, "pk": availability_rule.pk},
        )
        response = auth_client.get(url)
        assert response.status_code == 200
        assert response.data["end_time"] == availability_rule.end_time

    def test_delete_rule(self, auth_client, availability_rule, event_type):
        url = reverse(
            "availability-rule-detail",
            kwargs={"event_type_id": event_type.pk, "pk": availability_rule.pk},
        )
        response = auth_client.delete(url)
        assert response.status_code == 204

    def test_non_owner_cannot_retrieve(
        self, api_client, other_user, availability_rule, event_type
    ):
        api_client.force_authenticate(user=other_user)
        url = reverse(
            "availability-rule-detail",
            kwargs={"event_type_id": event_type.pk, "pk": availability_rule.pk},
        )
        response = api_client.get(url)
        assert response.status_code == 404

    def test_non_owner_cannot_delete(
        self, api_client, other_user, availability_rule, event_type
    ):
        api_client.force_authenticate(user=other_user)
        url = reverse(
            "availability-rule-detail",
            kwargs={"event_type_id": event_type.pk, "pk": availability_rule.pk},
        )
        response = api_client.delete(url)
        assert response.status_code == 404
