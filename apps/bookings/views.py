from rest_framework import viewsets, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from apps.bookings.serializers import CreateBookingSerializer
from rest_framework.response import Response
from apps.bookings.services import BookingService

class BookingViewSet(viewsets.ModelViewSet):
    
    def get_permissions(self):
        if self.action == "create":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        if self.action == "create":
            serializer_class = CreateBookingSerializer
            return serializer_class
        
    def create(self, request):
        data = request.data.copy()
        header_key = request.headers.get('Idempotency-key')
        if header_key:
            data['idempotency_key'] = header_key
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        booking, created = BookingService.create_booking(
            start_time=data['start_time'],
            end_time=data['end_time'],
            event_type=data['event_type'],
            invitee_name=data['invitee_name'],
            invitee_email=data['invitee_email'],
            invitee_timezone=data['invitee_timezone'],
            invitee_notes=data.get('invitee_notes'),
            idempotency_key=data['idempotency_key'],
            user=request.user,
        )
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response({'id': str(booking.id), 'detail': 'Booking created successfully'}, status=status_code)

