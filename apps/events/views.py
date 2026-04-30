from apps.events.models import EventType
from rest_framework import viewsets, status  
from rest_framework.response import Response 
from apps.events.serializers import (EventTypeSerializer, EventTypeListSerializer, 
                                     EventTypeDetailSerializer, EventTypeUpdateSerializer)
from django.shortcuts import get_object_or_404
from rest_framework.renderers import JSONRenderer, BrowsableAPIRenderer

class EventTypeViewSet(viewsets.ModelViewSet):
    permission_classes = []
    renderer_classes = [BrowsableAPIRenderer, JSONRenderer]

    def get_serializer(self, *args, **kwargs):

        if self.action == 'create':
            serializer_class = [EventTypeSerializer]

        elif self.action == "list":
            serializer_class = [EventTypeListSerializer]
        
        elif self.action == "retrieve":
            serializer_class = [EventTypeDetailSerializer]

        elif self.action in ["update", "partial_update"]:
            serializer_class = [EventTypeUpdateSerializer]

        elif self.action == "destroy":
            serializer_class = [EventTypeDetailSerializer]
    
    def create(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid(raise_exception=True):
            return Response({'detail': 'Event Type created successfully'}, status=status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    def list(self, request):
        queryset = EventType.objects.select_related('event_type').all()
        serializer = self.serializer_class(queryset, many=True, data=request.data)
        if serializer.is_valid(raise_exception=True):
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, pk=None):
        queryset = EventType.objects.select_related('event_type').all()
        event_type = get_object_or_404(queryset, pk=id)
        serializer = self.serializer_class(event_type, data=request.data)
        if serializer.is_valid(raise_exception=True):
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
        
    def update(self, request, pk=None):
        queryset = EventType.objects.select_related('event_type').all()
        event_type = get_object_or_404(queryset, pk=id)
        serializer = self.serializer_class(event_type, data=request.data)
        if serializer.is_valid(raise_exception=True):
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        serializer = self.serializer_class(data=request.data)
        event_type = EventType.objects.get(pk=id)
        if serializer.is_valid(raise_exception=True):
            event_type.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)