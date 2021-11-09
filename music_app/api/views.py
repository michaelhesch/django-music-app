from django.shortcuts import render
from django.http import JsonResponse

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


class GetRoom(APIView):
    serializer_class = RoomSerializer
    lookup_url_kwarg = 'code'

    # When calling GetRoom with GET request, pass in code param
    def get(self, request, format=None):
        code = request.GET.get(self.lookup_url_kwarg)
        if code != None:
            room = Room.objects.filter(code=code)
            if len(room) > 0:
                # Serialize the room value, get it in data format
                data = RoomSerializer(room[0]).data
                # Check if current session key = host session key to determine if user is host
                data['is_host'] = self.request.session.session_key == room[0].host
                return Response(data, status=status.HTTP_200_OK)
            return Response({'Room Not Found': 'Invalid Room Code'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({'Bad Request': 'Code parameter not found in request.'}, status=status.HTTP_400_BAD_REQUEST)


class GetRoom(APIView):
    serializer_class = RoomSerializer
    lookup_url_kwarg = 'code'

    def get(self, request, format=None):
        code = request.GET.get(self.lookup_url_kwarg)
        if code != None:
            room = Room.objects.filter(code=code)
            if len(room) > 0:
                data = RoomSerializer(room[0]).data
                data['is_host'] = self.request.session.session_key == room[0].host
                return Response(data, status=status.HTTP_200_OK)
            return Response({'Room Not Found': 'Invalid Room Code.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'Bad Request': 'Code paramater not found in request'}, status=status.HTTP_400_BAD_REQUEST)


class JoinRoom(APIView):
    # Create variable to hold room code
    lookup_url_kwarg = 'code'

    def post(self, request, format=None):
        # Check if current user has an active session with server
        if not self.request.session.exists(self.request.session.session_key):
            # Create new session if one does not exist
            self.request.session.create()
        # Get room code from post request
        code = request.data.get(self.lookup_url_kwarg)
        if code != None:
            room_result = Room.objects.filter(code=code)
            if len(room_result) > 0:
                room = room_result[0]
                # Record the room so if user returns later they can be added to the same room
                # Creates a temporary object called room_code to hold the room code
                self.request.session['room_code'] = code
                return Response({'message': 'Room Joined!'}, status=status.HTTP_200_OK)
            return Response({'Bad Request': 'Invalid Room Code'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'Bad Request': 'Invalid post data, did not find code'}, status=status.HTTP_400_BAD_REQUEST)


# Passing APIView model allows us to over-ride default methods
class CreateRoomView(APIView):
    serializer_class = CreateRoomSerializer

    def post(self, request, format=None):
        # Check if current user has an active session with server
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
                # Creates a temporary object called room_code to hold the room code
                self.request.session['room_code'] = room.code
                return Response(RoomSerializer(room).data, status=status.HTTP_200_OK)
            else:
                room = Room(host=host, guest_can_pause=guest_can_pause,
                            votes_to_skip=votes_to_skip)
                room.save()
                # Creates a temporary object called room_code to hold the room code
                self.request.session['room_code'] = room.code
                return Response(RoomSerializer(room).data, status=status.HTTP_201_CREATED)

        return Response({'Bad Request': 'Invalid data...'}, status=status.HTTP_400_BAD_REQUEST)


class UserInRoom(APIView):
    # Checks get request from front end and returns room code if
    # the user is currently in a session/room.
    def get(self, request, format=None):
        # Check if current user has an active session with server
        if not self.request.session.exists(self.request.session.session_key):
            # Create new session if one does not exist
            self.request.session.create()
        # Check current session for a room code
        data = {
            'code': self.request.session.get('room_code'),
        }
        # Return data to front end as a JSON response
        # If user is not in a room this will return None
        return JsonResponse(data, status=status.HTTP_200_OK)


class LeaveRoom(APIView):
    def post(self, request, format=None):
        if 'room_code' in self.request.session:
            # Remove room code from the session if it exists
            self.request.session.pop('room_code')
            # Check if session user is room owner, delete room if true
            host_id = self.request.session.session_key
            room_results = Room.objects.filter(host=host_id)
            if len(room_results) > 0:
                room = room_results[0]
                room.delete()

        return Response({'Message': 'Success'}, status=status.HTTP_200_OK)
