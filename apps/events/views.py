from apps.events.models import EventType
from rest_framework import viewsets, status  
from rest_framework.response import Response 
from apps.events.serializers import (EventTypeSerializer, EventTypeListSerializer, 
                                     EventTypeDetailSerializer, EventTypeUpdateSerializer)
from django.shortcuts import get_object_or_404
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer
from rest_framework.permissions import IsAuthenticated
from apps.events.permissions import IsEventTypeOwner

class EventTypeViewSet(viewsets.ModelViewSet):
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer]

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
    
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save(owner=request.user)
            return Response({'detail': 'Event Type created successfully'}, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request):
        queryset = EventType.objects.filter(owner=request.user)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def retrieve(self, request, pk=None):
        queryset = EventType.objects.select_related('owner').all()
        event_type = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(request, event_type)
        serializer = self.get_serializer(event_type)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    def update(self, request, pk=None):
        queryset = EventType.objects.select_related('owner').all()
        event_type = get_object_or_404(queryset, pk=pk)
        self.check_object_permissions(request, event_type)
        serializer = self.get_serializer(event_type, data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        event_type = get_object_or_404(EventType, pk=pk)
        self.check_object_permissions(request, event_type)
        event_type.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
