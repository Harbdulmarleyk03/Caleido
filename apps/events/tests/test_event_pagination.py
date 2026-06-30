from apps.events.tests.factories import EventTypeFactory
import pytest
from django.urls import reverse


@pytest.mark.django_db
class TestEventTypeListPagination:

    def test_first_page_has_next_cursor_when_results_exceed_page_size(
        self, owner, api_client
    ):
        EventTypeFactory.create_batch(25, owner=owner)
        api_client.force_authenticate(user=owner)
        url = reverse("event-type-list")
        response = api_client.get(url)
        assert response.status_code == 200
        assert response.data["next"] is not None
        assert response.data["previous"] is None

    def test_results_key_exists_in_response(self, owner, api_client):
        EventTypeFactory.create_batch(25, owner=owner)
        api_client.force_authenticate(user=owner)
        url = reverse("event-type-list")
        response = api_client.get(url)
        assert "results" in response.data
