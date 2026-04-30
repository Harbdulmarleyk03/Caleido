from django.shortcuts import render
from rest_framework import viewsets 

class EventTypeViewSet(viewsets.ModelViewSet):
    permission_classes = []
    