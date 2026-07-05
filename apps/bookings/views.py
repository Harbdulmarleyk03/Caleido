from rest_framework import viewsets, status, mixins
from rest_framework.permissions import AllowAny, IsAuthenticated
from apps.bookings.models import Booking
from apps.bookings.serializers import (
    CreateBookingSerializer,
    RescheduleBookingSerializer,
    BookingSerializer,
)
from rest_framework.response import Response
from apps.bookings.services import BookingService
from django_filters.rest_framework import DjangoFilterBackend
from apps.bookings.filters import BookingFilter
from rest_framework.filters import OrderingFilter
from rest_framework.decorators import action
from common.pagination import BookmarkCursorPagination
from apps.bookings.permissions import (
    CancelBookingPermission,
    RescheduleBookingPermission,
)
from datetime import timedelta
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from apps.bookings.ical import IcalExportService
from drf_spectacular.utils import extend_schema, OpenApiResponse
from drf_spectacular.types import OpenApiTypes


class BookingViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    # Deliberately NOT ModelViewSet — that bundles UpdateModelMixin and
    # DestroyModelMixin, which would wire PUT/PATCH/DELETE onto the base
    # /bookings/{id}/ route. Bookings are never overwritten wholesale or
    # hard-deleted; they're only ever cancelled or rescheduled via the
    # explicit @action endpoints below. Before this fix, a PUT/PATCH/DELETE
    # to the base detail route would reach get_serializer_class(), fall
    # through its implicit `return None` for unhandled actions, and crash
    # with 'NoneType' object is not callable — a real 500 in production,
    # not just a schema-generation artifact. Only inheriting the mixins we
    # actually support means DRF's router now returns a correct 405 Method
    # Not Allowed for those verbs instead.
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = BookingFilter
    ordering_fields = ["start_time", "id"]
    ordering = ["-start_time"]
    pagination_class = BookmarkCursorPagination

    def get_permissions(self):
        if self.action == "create":
            permission_classes = [AllowAny]
        elif self.action == "cancel":
            permission_classes = [CancelBookingPermission]
        elif self.action == "reschedule":
            permission_classes = [RescheduleBookingPermission]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        if self.action == "create":
            return CreateBookingSerializer
        elif self.action in ["list", "retrieve"]:
            return BookingSerializer
        elif self.action == "reschedule":
            return RescheduleBookingSerializer
        elif self.action == "cancel":
            return BookingSerializer  # no body; used for schema/introspection only
        return BookingSerializer

    def create(self, request):
        data = request.data.copy()
        header_key = request.headers.get("Idempotency-key")
        if header_key:
            data["idempotency_key"] = header_key
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        booking, created = BookingService.create_booking(
            start_time=data["start_time"],
            end_time=data["end_time"],
            event_type=data["event_type"],
            invitee_name=data["invitee_name"],
            invitee_email=data["invitee_email"],
            invitee_timezone=data["invitee_timezone"],
            invitee_notes=data.get("invitee_notes"),
            idempotency_key=data["idempotency_key"],
            user=request.user,
        )
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(
            {"id": str(booking.id), "detail": "Booking created successfully"},
            status=status_code,
        )

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Booking.objects.none()
        return Booking.objects.filter(
            event_type__owner=self.request.user
        ).select_related("event_type", "invitee")

    @action(
        detail=True,
        methods=["patch"],
        url_path="cancel",
        permission_classes=[CancelBookingPermission],
    )
    @extend_schema(
        request=None, responses={200: OpenApiResponse(description="Cancelled")}
    )
    def cancel(self, request, pk=None):
        booking = get_object_or_404(Booking.objects.select_related("event_type"), pk=pk)
        self.check_object_permissions(request, booking)
        BookingService.cancel_booking(booking=booking, user=request.user)
        return Response({"status": "Cancelled"}, status=status.HTTP_200_OK)

    @action(
        detail=True,
        methods=["patch"],
        url_path="reschedule",
        permission_classes=[RescheduleBookingPermission],
    )
    @extend_schema(responses={200: OpenApiResponse(description="Rescheduled")})
    def reschedule(self, request, pk=None):
        booking = get_object_or_404(Booking.objects.select_related("event_type"), pk=pk)
        self.check_object_permissions(request, booking)
        serializer = RescheduleBookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        start_time = data["start_time"]
        end_time = start_time + timedelta(minutes=booking.event_type.duration_minutes)
        BookingService.reschedule_booking(
            booking=booking, user=request.user, start_time=start_time, end_time=end_time
        )
        return Response({"status": "Rescheduled"}, status=status.HTTP_200_OK)


class BookingIcalView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        responses={
            (200, "text/calendar"): OpenApiResponse(
                response=OpenApiTypes.BINARY,
                description="RFC 5545 .ics file for this booking, served as a download.",
            ),
            403: OpenApiResponse(
                description="Requester is not the owner of this booking's event type."
            ),
            404: OpenApiResponse(description="Booking not found."),
        },
        description="Exports a single booking as a downloadable .ics calendar file.",
    )
    def get(self, request, booking_id):
        booking = get_object_or_404(
            Booking.objects.select_related("event_type__owner", "invitee"),
            id=booking_id,
        )
        if booking.event_type.owner != request.user:
            raise PermissionDenied("You do not have permission to access this booking.")
        ical_content = IcalExportService.generate_booking_ical(booking)
        response = HttpResponse(ical_content, content_type="text/calendar")
        response["Content-Disposition"] = (
            f"attachment; filename=booking_{booking.id}.ics"
        )
        return response
