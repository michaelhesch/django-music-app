from django.shortcuts import render
from django.http import HttpResponse
from rest_framework import generics

from api.serializers import RoomSerializer

from .models import Room
from .serializers import RoomSerializer


# API view to return list of all available rooms
class RoomView(generics.CreateAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
