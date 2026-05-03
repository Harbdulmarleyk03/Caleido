from apps.events.models import EventType, AvailabilityRule
from rest_framework import viewsets, status, generics   
from rest_framework.response import Response 
from apps.events.serializers import (EventTypeSerializer, EventTypeListSerializer, 
            EventTypeDetailSerializer, EventTypeUpdateSerializer, AvailabilityRuleSerializer)
from django.shortcuts import get_object_or_404
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.permissions import IsAuthenticated
from apps.events.permissions import IsEventTypeOwner, IsAvailabilityRuleOwner
from apps.events.services.availability_service import AvailabilityScheduleService

class EventTypeViewSet(viewsets.ModelViewSet):
    renderer_classes = [JSONRenderer, BrowsableAPIRenderer]

    def get_permissions(self):
   
        if self.action in ['list', 'create']:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticated, IsEventTypeOwner]
        return [permission() for permission in permission_classes]

    def get_serializer_class(self, *args, **kwargs):

        if self.action == 'create':
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
            return Response({'detail': 'Event Type created successfully'}, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request):
        queryset = self.get_queryset()
        is_active = request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def retrieve(self, request, pk=None):
        queryset = EventType.objects.select_related('owner').all()
        event_type = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(request, event_type)
        serializer = self.get_serializer(event_type)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    def update(self, request, pk=None, **kwargs):
        partial = kwargs.pop('partial', False)  # captures partial=True from PATCH
        queryset = EventType.objects.select_related('owner').all()
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

class AvailabilityScheduleListView(generics.ListCreateAPIView):
    serializer_class = AvailabilityRuleSerializer
    permission_classes = [IsAuthenticated, IsAvailabilityRuleOwner]
    renderer_classes = [BrowsableAPIRenderer]

    def get_queryset(self):
        event_type_id = self.kwargs.get('event_type_id')
        queryset = AvailabilityRule.objects.filter(event_type__id=event_type_id, event_type__owner=self.request.user).select_related(
            'event_type', 'event_type__owner')
        return queryset

    def perform_create(self, serializer):
        event_type_id = self.kwargs.get('event_type_id')
        event_type = get_object_or_404(EventType, pk=event_type_id, owner=self.request.user)
        AvailabilityScheduleService.create_availability_rule(event_type=event_type,**serializer.validated_data)
        
class AvailabilityScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = AvailabilityRuleSerializer
    permission_classes = [IsAuthenticated, IsAvailabilityRuleOwner]
    
    def get_queryset(self):
        return AvailabilityRule.objects.select_related('event_type').filter(event_type__owner=self.request.user, event_type_id=self.kwargs['event_type_id'])
    
    def perform_update(self, serializer):
        AvailabilityScheduleService.update_availability_rule(
            availability_rule_id=serializer.instance.id,
            **serializer.validated_data
        )