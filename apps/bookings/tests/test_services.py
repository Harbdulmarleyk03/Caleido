import pytest 
from apps.bookings.services import BookingService
from unittest.mock import patch
from datetime import timedelta
from django.utils import timezone

@pytest.mark.django_db(transaction=True)
class TestScheduleBookingReminder:

    @patch('apps.bookings.services.send_booking_reminder_email.apply_async')
    def test_schedules_both_reminders_for_booking_more_than_24_hours_away(self, mock_apply_async, booking_with_invitee):
        mock_apply_async.return_value.id = "fake-task-id"
        BookingService.schedule_booking_reminder(str(booking_with_invitee.id))
        reminder_24h_eta = booking_with_invitee.start_time - timedelta(hours=24)
        reminder_1h_eta = booking_with_invitee.start_time - timedelta(hours=1)
        mock_apply_async.assert_any_call(args=[str(booking_with_invitee.id), "24h"], eta=reminder_24h_eta)
        mock_apply_async.assert_any_call(args=[str(booking_with_invitee.id), "1h"], eta=reminder_1h_eta)

    @patch('apps.bookings.services.send_booking_reminder_email.apply_async')
    def test_schedules_only_one_hour_reminder_when_twenty_four_hour_window_has_passed(self, mock_apply_async, booking_with_invitee):
        booking_with_invitee.start_time = timezone.now() + timedelta(hours=2)
        booking_with_invitee.save()
        reminder_1h_eta = booking_with_invitee.start_time - timedelta(hours=1)
        mock_apply_async.return_value.id = "fake-task-id"
        BookingService.schedule_booking_reminder(str(booking_with_invitee.id))
        mock_apply_async.assert_any_call(args=[str(booking_with_invitee.id), "1h"], eta=reminder_1h_eta)

    @patch('apps.bookings.services.send_booking_reminder_email.apply_async')
    def test_does_not_schedule_reminders_for_imminent_booking(self, mock_apply_async, booking_with_invitee):
        booking_with_invitee.start_time = timezone.now() + timedelta(minutes=30)
        booking_with_invitee.save()
        mock_apply_async.return_value.id = "fake-task-id"
        BookingService.schedule_booking_reminder(str(booking_with_invitee.id))
        mock_apply_async.assert_not_called() 
        mock_apply_async.assert_not_called()

    @patch('apps.bookings.services.send_booking_reminder_email.apply_async')
    def test_persists_scheduled_reminder_task_ids(self, mock_apply_async, booking_with_invitee):
        mock_apply_async.return_value.id = "fake-task-id"
        BookingService.schedule_booking_reminder(str(booking_with_invitee.id))

        booking_with_invitee.refresh_from_db()
        assert booking_with_invitee.reminder_24h_task_id is not None
        assert booking_with_invitee.reminder_1h_task_id is not None
        mock_apply_async.assert_called()

@pytest.mark.django_db(transaction=True)
class TestCancelBooking:

    @patch('apps.bookings.services.app.control.revoke')
    @patch('apps.bookings.services.send_booking_cancellation_email.delay')
    def test_cancellation_revokes_pending_reminders(self, mock_revoke, mock_delay, booking_with_invitee):
        booking_with_invitee.reminder_24h_task_id = "fake-task-id-24h"
        booking_with_invitee.reminder_1h_task_id = "fake-task-id-1h"
        booking_with_invitee.save()
        BookingService.cancel_booking(booking_with_invitee, user=None)
        mock_revoke.assert_called()
        mock_delay.assert_called()

    @patch('apps.bookings.services.send_booking_cancellation_email.delay')
    @patch('apps.bookings.services.app.control.revoke')
    def test_cancellation_clears_stored_reminder_task_ids(self, mock_revoke, mock_delay, booking_with_invitee):
        booking_with_invitee.reminder_24h_task_id = "fake-task-id-24h"
        booking_with_invitee.reminder_1h_task_id = "fake-task-id-1h"
        booking_with_invitee.save()
        BookingService.cancel_booking(booking_with_invitee, user=None)
        booking_with_invitee.refresh_from_db()
        assert booking_with_invitee.reminder_24h_task_id is None 
        assert booking_with_invitee.reminder_1h_task_id is None 
        mock_revoke.assert_called()
        mock_delay.assert_any_call(str(booking_with_invitee.id))

    @patch('apps.bookings.services.send_booking_cancellation_email.delay')
    def test_cancellation_notifies_invitee(self, mock_delay, booking_with_invitee):
        BookingService.cancel_booking(booking_with_invitee, user=None)
        mock_delay.assert_any_call(str(booking_with_invitee.id))

@pytest.mark.django_db(transaction=True)
class TestRescheduleBooking:

    @patch('apps.bookings.services.BookingService.schedule_booking_reminder')
    @patch('apps.bookings.services.app.control.revoke')
    @patch('apps.bookings.services.send_booking_reschedule_email.delay')
    def test_reschedule_revokes_previously_scheduled_reminders(self, mock_delay, mock_revoke, mock_schedule, booking_with_invitee):
        booking_with_invitee.reminder_24h_task_id = "fake-task-id-24h"
        booking_with_invitee.reminder_1h_task_id = "fake-task-id-1h"
        booking_with_invitee.save()
        BookingService.reschedule_booking(booking_with_invitee, user=None, start_time=booking_with_invitee.start_time, end_time=booking_with_invitee.end_time)
        booking_with_invitee.refresh_from_db()
        mock_delay.assert_called()
        mock_revoke.assert_called()
        mock_schedule.assert_called()

    @patch('apps.bookings.services.BookingService.schedule_booking_reminder')
    @patch('apps.bookings.services.app.control.revoke')
    @patch('apps.bookings.services.send_booking_reschedule_email.delay')
    def test_reschedule_schedules_reminders_for_new_booking_time(self, mock_delay, mock_revoke, mock_schedule, booking_with_invitee):
        booking_with_invitee.refresh_from_db()
        booking_with_invitee.reminder_24h_task_id = "fake-task-id-24h"
        booking_with_invitee.reminder_1h_task_id = "fake-task-id-1h"
        booking_with_invitee.save()
        BookingService.reschedule_booking(booking_with_invitee, user=None, start_time=booking_with_invitee.start_time, end_time=booking_with_invitee.end_time)
        mock_revoke.assert_any_call("fake-task-id-24h", terminate=False)
        mock_revoke.assert_any_call("fake-task-id-1h", terminate=False)
        mock_delay.assert_called()
        mock_schedule.assert_called_once_with(str(booking_with_invitee.id))

    @patch('apps.bookings.services.send_booking_reschedule_email.delay')
    @patch('apps.bookings.services.app.control.revoke')
    def test_reschedule_notifies_invitee_of_updated_schedule(self, mock_delay, mock_revoke, booking_with_invitee):
        booking_with_invitee.refresh_from_db()
        booking_with_invitee.reminder_24h_task_id = "fake-task-id-24h"
        booking_with_invitee.reminder_1h_task_id = "fake-task-id-1h"
        booking_with_invitee.save()
        BookingService.reschedule_booking(booking_with_invitee, user=None, start_time=booking_with_invitee.start_time, end_time=booking_with_invitee.end_time)
        mock_delay.assert_called()
        mock_revoke.assert_called()
