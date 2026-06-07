import pytest
from django.core import mail
from django.test import override_settings
from unittest.mock import patch
from apps.bookings.tasks import send_booking_confirmation_email, send_booking_cancellation_email, send_booking_reschedule_email, send_booking_reminder_email
import uuid 

@pytest.mark.django_db
class TestSendBookingConfirmationEmail:
    
    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_booking_confirmed_sends_two_emails(self, booking_with_invitee):
        
        send_booking_confirmation_email(str(booking_with_invitee.id))

        assert len(mail.outbox) == 2
        recipients = [msg.to[0] for msg in mail.outbox]
        assert booking_with_invitee.invitee.email in recipients
        assert booking_with_invitee.event_type.owner.email in recipients

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_booking_confirmed_skips_when_not_confirmed(self, booking_with_invitee):
        booking_with_invitee.status = "cancelled"
        booking_with_invitee.save()

        send_booking_confirmation_email(str(booking_with_invitee.id))
        assert len(mail.outbox) == 0

    def test_send_booking_confirmed_booking_not_found(self, caplog):
        fake_id = str(uuid.uuid4())

        send_booking_confirmation_email(fake_id)
        assert "not found" in caplog.text 
        assert len(mail.outbox) == 0

@pytest.mark.django_db
class TestSendBookingCancellationEmail:

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_booking_cancellation_sends_two_emails(self, booking_with_invitee):
        booking_with_invitee.status = 'cancelled'
        booking_with_invitee.save()

        send_booking_cancellation_email(str(booking_with_invitee.id))

        assert len(mail.outbox) == 2
        recipients = [msg.to[0] for msg in mail.outbox]
        assert booking_with_invitee.invitee.email in recipients
        assert booking_with_invitee.event_type.owner.email in recipients

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_booking_cancellation_skips_when_not_cancelled(self, booking_with_invitee):
        
        send_booking_cancellation_email(str(booking_with_invitee.id))

        assert len(mail.outbox) == 0

    def test_send_booking_cancellation_not_found(self, caplog):
        fake_id = str(uuid.uuid4())

        send_booking_cancellation_email(fake_id)

        assert "not found when sending cancellation email" in caplog.text 
        assert len(mail.outbox) == 0


@pytest.mark.django_db
class TestSendBookingRescheduleEmail:

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_booking_rescheduled_sends_two_emails(self, booking_with_invitee):

        send_booking_reschedule_email(str(booking_with_invitee.id))

        assert len(mail.outbox) == 2
        recipients = [msg.to[0] for msg in mail.outbox]
        assert booking_with_invitee.invitee.email in recipients
        assert booking_with_invitee.event_type.owner.email in recipients

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_booking_rescheduled_skips_when_not_confirmed(self, booking_with_invitee):
        booking_with_invitee.status = "cancelled"
        booking_with_invitee.save()

        send_booking_reschedule_email(str(booking_with_invitee.id))

        assert len(mail.outbox) == 0

    def test_send_booking_rescheduled_not_found(self, caplog):
        fake_id = str(uuid.uuid4())

        send_booking_reschedule_email(fake_id)

        assert "not found when sending reschedule email" in caplog.text 
        assert len(mail.outbox) == 0

    def test_send_booking_rescheduled_fall_back_with_no_audit(self, booking_with_invitee):

        send_booking_reschedule_email(str(booking_with_invitee.id))
        assert any("unknown" in msg.body for msg in mail.outbox)

@pytest.mark.django_db
class TestSendBookingReminderEmail:

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_booking_reminder_sends_two_emails(self, booking_with_invitee):

        send_booking_reminder_email(str(booking_with_invitee.id), "24h")
        send_booking_reminder_email(str(booking_with_invitee.id), "1h")

        assert len(mail.outbox) == 4
        recipients = [msg.to[0] for msg in mail.outbox]
        assert booking_with_invitee.invitee.email in recipients
        assert booking_with_invitee.event_type.owner.email in recipients

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_send_booking_reminder_skips_when_not_confirmed(self, booking_with_invitee):
        booking_with_invitee.status = "cancelled"
        booking_with_invitee.save()

        send_booking_reminder_email(str(booking_with_invitee.id), "24h")
        send_booking_reminder_email(str(booking_with_invitee.id), "1h")

        assert len(mail.outbox) == 0

    def test_send_booking_reminder_not_found(self, caplog):
        fake_id = str(uuid.uuid4())

        send_booking_reminder_email(fake_id, '24h')

        assert "not found when sending reminder email" in caplog.text 
        assert len(mail.outbox) == 0

    def test_send_booking_reminder_24h_message_body(self, booking_with_invitee):

        send_booking_reminder_email(str(booking_with_invitee.id), "24h")

        assert any("24h" in msg.body for msg in mail.outbox)

    def test_send_booking_reminder_1h_message_body(self, booking_with_invitee):

        send_booking_reminder_email(str(booking_with_invitee.id), "1h")

        assert any("1h" in msg.body for msg in mail.outbox)

    