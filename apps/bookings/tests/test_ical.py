import pytest 

class TestIcalService:

    def test_ical_contains_correct_summary(self, owner, auth_client, booking_with_invitee):
        pass 

    def test_ical_contains_correct_dtstart_and_dtend(self):
        pass 


    def test_ical_contains_uid(self):
        pass 


    def test_cancelled_booking_has_cancelled_status(self):
        pass 


    def test_confirmed_booking_has_confirmed_status(self):
        pass 


class TestBookingIcalView:

    def test_ical_response_has_correct_content_type(self):
        pass 

    def test_ical_response_has_correct_content_disposition(self):
        pass 

    def test_unauthenticated_returns_401(self):
        pass 

    def test_non_owner_returns_403(self):
        pass 

    def test_nonexistent_booking_returns_404(self):
        pass 