import pytest 

@pytest.mark.django_db(transaction=True)
class TestBookingService:

    def test_create_booking():
        pass 

    def test_cancel_booking():
        pass 

    def test_reschedule_booking():
        pass 

    def test_schedule_booking_reminder():
        pass 