from rest_framework import permissions
from apps.bookings.tokens import verify_cancel_token, verify_reschedule_token


class CancelBookingPermission(permissions.BasePermission):

    def has_permission(self, request, view):

        if request.user and request.user.is_authenticated:
            return True

        token = request.data.get("token") or request.query_params.get("token")

        if not token:
            return False

        try:
            booking_id = verify_cancel_token(token)

            return booking_id

        except ValueError:
            return False

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated:
            return obj.event_type.owner == request.user

        token = request.data.get("token") or request.query_params.get("token")

        if not token:
            return False

        try:
            booking = verify_cancel_token(token)

            return booking.id == obj.id

        except ValueError:
            return False


class RescheduleBookingPermission(permissions.BasePermission):

    def has_permission(self, request, view):

        if request.user and request.user.is_authenticated:
            return True

        token = request.data.get("token") or request.query_params.get("token")

        if not token:
            return False

        try:
            booking_id = verify_reschedule_token(token)

            return booking_id

        except ValueError:
            return False

    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_authenticated:
            return obj.event_type.owner == request.user

        token = request.data.get("token") or request.query_params.get("token")

        if not token:
            return False

        try:
            booking = verify_reschedule_token(token)

            return booking.id == obj.id

        except ValueError:
            return False
