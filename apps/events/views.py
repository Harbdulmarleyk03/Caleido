from datetime import datetime
from apps.events.models import EventType, AvailabilityRule, DateOverride
from rest_framework import viewsets, status, generics
from rest_framework.response import Response
from apps.events.serializers import (
    EventTypeSerializer,
    EventTypeListSerializer,
    EventTypeDetailSerializer,
    EventTypeUpdateSerializer,
    AvailabilityRuleSerializer,
    DateOverrideSerializer,
)
from django.shortcuts import get_object_or_404
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.permissions import AllowAny, IsAuthenticated
from apps.events.permissions import IsEventTypeOwner, IsNestedResourceOwner
from apps.events.services.availability_service import AvailabilityRuleService
from apps.events.services.date_override_service import DateOverrideService
from rest_framework.views import APIView
from apps.events.slot_engine import generate_slots
from apps.bookings.models import Booking
from rest_framework.exceptions import ValidationError
import pytz
from apps.events.services.slot_cache_service import SlotCacheService
from common.pagination import (
    AvailabilityRuleCursorPagination,
    DateOverrideCursorPagination,
    EventTypeCursorPagination,
)


# Event Type Views
class EventTypeViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]
    pagination_class = EventTypeCursorPagination

    def get_permissions(self):

        if self.action in ["list", "create"]:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsEventTypeOwner]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self, *args, **kwargs):

        if self.action == "create":
            serializer_class = EventTypeSerializer
            return serializer_class

        elif self.action == "list":
            serializer_class = EventTypeListSerializer
            return serializer_class

        elif self.action == "retrieve":
            serializer_class = EventTypeDetailSerializer
            return serializer_class

        elif self.action in ["update", "partial_update"]:
            serializer_class = EventTypeUpdateSerializer
            return serializer_class
        return EventTypeSerializer

    def get_queryset(self):
        return EventType.objects.filter(owner=self.request.user)

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save(owner=request.user)
            return Response(
                {"detail": "Event Type created successfully"},
                status=status.HTTP_201_CREATED,
            )
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def list(self, request):
        queryset = self.get_queryset()
        is_active = request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        queryset = EventType.objects.select_related("owner").all()
        event_type = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(request, event_type)
        serializer = self.get_serializer(event_type)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def update(self, request, pk=None, **kwargs):
        partial = kwargs.pop("partial", False)  # captures partial=True from PATCH
        queryset = EventType.objects.select_related("owner").all()
        event_type = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(request, event_type)
        serializer = self.get_serializer(event_type, data=request.data, partial=partial)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        event_type = get_object_or_404(EventType, pk=pk)
        self.check_object_permissions(request, event_type)
        event_type.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# Availability Rules Views
class AvailabilityRuleListCreateView(generics.ListCreateAPIView):
    serializer_class = AvailabilityRuleSerializer
    permission_classes = [IsAuthenticated, IsNestedResourceOwner]
    pagination_class = AvailabilityRuleCursorPagination

    def get_event_type(self):
        # Cache on the request cycle so we don't hit the DB twice
        if not hasattr(self, "_event_type"):
            self._event_type = get_object_or_404(
                EventType, pk=self.kwargs["event_type_id"], owner=self.request.user
            )
        return self._event_type

    def get_serializer_context(self):
        # Injects event_type so the serializer can do overlap validation
        context = super().get_serializer_context()
        context["event_type"] = self.get_event_type()
        return context

    def get_queryset(self):
        return AvailabilityRule.objects.filter(event_type=self.get_event_type())

    def perform_create(self, serializer):
        AvailabilityRuleService.create_availability_rule(
            event_type=self.get_event_type(),
            validated_data=serializer.validated_data,
        )


class AvailabilityRuleDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = AvailabilityRuleSerializer
    permission_classes = [IsAuthenticated, IsNestedResourceOwner]

    def get_queryset(self):
        return AvailabilityRule.objects.select_related("event_type").filter(
            event_type__owner=self.request.user,
            event_type_id=self.kwargs["event_type_id"],
        )


class DateOverrideListCreateView(generics.ListCreateAPIView):
    serializer_class = DateOverrideSerializer
    permission_classes = [IsAuthenticated, IsNestedResourceOwner]
    pagination_class = DateOverrideCursorPagination

    def get_event_type(self):
        # Cache on the request cycle so we don't hit the DB twice
        if not hasattr(self, "_event_type"):
            self._event_type = get_object_or_404(
                EventType, pk=self.kwargs["event_type_id"], owner=self.request.user
            )
        return self._event_type

    def get_serializer_context(self):
        # Injects event_type so the serializer can do overlap validation
        context = super().get_serializer_context()
        context["event_type"] = self.get_event_type()
        return context

    def get_queryset(self):
        return DateOverride.objects.filter(event_type=self.get_event_type())

    def perform_create(self, serializer):
        DateOverrideService.create_date_override(
            event_type=self.get_event_type(),
            validated_data=serializer.validated_data,
        )


class DateOverrideDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = DateOverrideSerializer
    permission_classes = [IsAuthenticated, IsNestedResourceOwner]

    def get_queryset(self):
        return DateOverride.objects.select_related("event_type").filter(
            event_type__owner=self.request.user,
            event_type_id=self.kwargs["event_type_id"],
        )


class SlotListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, event_type_id):
        date_str = request.query_params.get("date")
        if date_str is None:
            raise ValidationError({"date": "Date is missing"})
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"error": "Invalid date format"}, status=status.HTTP_400_BAD_REQUEST
            )
        timezone = request.query_params.get("timezone", "UTC")
        if timezone not in pytz.all_timezones:
            raise ValidationError({"timezone": "Invalid timezone"})
        event_type = get_object_or_404(
            EventType.objects.select_related("owner"), pk=event_type_id, is_active=True
        )

        def compute():
            rules = AvailabilityRule.objects.filter(event_type=event_type).values()
            overrides = DateOverride.objects.filter(event_type=event_type).values()
            bookings = Booking.objects.filter(
                event_type=event_type, status="confirmed", start_time__date=target_date
            ).values("start_time", "end_time")
            duration = event_type.duration_minutes
            buffer_before = event_type.buffer_before_min
            buffer_after = event_type.buffer_after_min
            min_notice_hours = event_type.min_notice_hours
            max_future_days = event_type.max_future_days
            owner_timezone = event_type.owner.timezone
            now = datetime.now(pytz.UTC)
            return generate_slots(
                rules,
                overrides,
                bookings,
                target_date,
                timezone,
                duration,
                buffer_before,
                buffer_after,
                min_notice_hours,
                max_future_days,
                owner_timezone,
                now,
            )

        owner_timezone = event_type.owner.timezone
        slots = SlotCacheService.get_slots(
            event_type_id=event_type_id,
            date=target_date.isoformat(),
            timezone=owner_timezone,
            generate_slots=compute,
        )
        response = Response({"slots": slots})
        response["Cache-Control"] = "public, max-age=60"
        return response
