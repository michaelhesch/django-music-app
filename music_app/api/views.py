from django.shortcuts import render
from rest_framework import generics, serializers, status

from rest_framework.views import APIView
from rest_framework.response import Response
from api.serializers import RoomSerializer, CreateRoomSerializer

from .models import Room
from .serializers import RoomSerializer


# API view to return list of all available rooms
class RoomView(generics.CreateAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer


# APIView model allows us to over-ride default methods
class CreateRoomView(APIView):
    serializer_class = CreateRoomSerializer

    def post(self, request, format=None):
        # Checking if current user has an active session with server
        if not self.request.session.exists(self.request.session.session_key):
            # Create new session if one does not exist
            self.request.session.create()

        # Use serializer function to generate python friendly data
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            guest_can_pause = serializer.data.get('guest_can_pause')
            votes_to_skip = serializer.data.get('votes_to_skip')
            host = self.request.session.session_key
            queryset = Room.objects.filter(host=host)
            # Check for an existing room owned by the current session host
            # If existing room, update to current request values
            if queryset.exists():
                room = queryset[0]
                room.guest_can_pause = guest_can_pause
                room.votes_to_skip = votes_to_skip
                room.save(update_fields=['guest_can_pause', 'votes_to_skip'])
            else:
                room = Room(host=host, guest_can_pause=guest_can_pause, votes_to_skip=votes_to_skip)
                room.save()

        return Response(RoomSerializer(room).data, status=status.HTTP_200_OK)
