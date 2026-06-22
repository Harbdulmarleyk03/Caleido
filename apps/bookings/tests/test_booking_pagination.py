import pytest 
from apps.bookings.tests.factories import BookingFactory
from apps.events.tests.factories import EventTypeFactory
from django.urls import reverse

@pytest.mark.django_db(transaction=True)
class TestBookingListPagination:

    def test_first_page_returns_next_cursor(self, owner, api_client):
        event_type = EventTypeFactory(owner=owner)
        BookingFactory.create_batch(25, event_type=event_type)
        api_client.force_authenticate(user=owner)
        response = api_client.get("/api/v1/bookings/")
        assert response.status_code == 200
        assert response.data['next'] is not None 
        assert response.data['previous'] is None 

    def test_second_page_returns_previous_cursor(self, owner, api_client):
        event_type = EventTypeFactory(owner=owner)
        BookingFactory.create_batch(25, event_type=event_type)
        api_client.force_authenticate(user=owner)
        print(reverse('booking-list'))
        url = reverse('booking-list')
        first_response = api_client.get(url)
        next_url = first_response.data['next']
        second_response = api_client.get(next_url)
        assert second_response.status_code == 200 
        assert second_response.data['previous'] is not None 

    def test_results_do_not_overlap_between_pages(self, owner, api_client):
        event_type = EventTypeFactory(owner=owner)
        BookingFactory.create_batch(25, event_type=event_type)
        api_client.force_authenticate(user=owner)
        first_response = api_client.get('/api/v1/bookings/')
        next_url = first_response.data['next']
        second_response = api_client.get(next_url)
        page1_ids = {item['id'] for item in first_response.data['results']}
        page2_ids = {item['id'] for item in second_response.data['results']}
        assert page1_ids.isdisjoint(page2_ids)
       

    def test_invalid_cursor_returns_404(self, owner, api_client):
        event_type = EventTypeFactory(owner=owner)
        BookingFactory(event_type=event_type)
        api_client.force_authenticate(user=owner)
        url = reverse('booking-list')
        response = api_client.get(url, {'cursor': 'garbage'})
        assert response.status_code == 404  # DRF CursorPagination raises NotFound
            