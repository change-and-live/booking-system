from rest_framework import serializers
from .models import Room, Booking, Facility
from django.contrib.auth import get_user_model
from .utils import validate_booking_times, check_booking_overlap

User = get_user_model()

class FacilitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Facility
        fields = ['id', 'name', 'description']

class RoomSerializer(serializers.ModelSerializer):
    facilities = FacilitySerializer(many=True, read_only=True)
    
    class Meta:
        model = Room
        fields = ['id', 'name', 'capacity', 'facilities']

class BookingSerializer(serializers.ModelSerializer):
    room = RoomSerializer(read_only=True)
    room_id = serializers.PrimaryKeyRelatedField(
        queryset=Room.objects.all(), 
        source='room',
        write_only=True,
        label = "Комната"
    )

    user = serializers.SlugRelatedField(
        slug_field='username',
        read_only=True
    )

    class Meta:
        model = Booking
        fields = [
            'id', 'room', 'room_id', 'user', 
            'start_time', 'end_time', 'status', 'created_at'
        ]
        read_only_fields = ['status', 'created_at', 'user']

    def validate(self, data):
        room = data.get('room')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        if self.instance:
            room = room or self.instance.room
            start_time = start_time or self.instance.start_time
            end_time = end_time or self.instance.end_time
        
        validate_booking_times(start_time, end_time)

        status = data.get('status')
        if status is None:
            if self.instance:
                status = self.instance.status
            else:
                status = 'active'
                
        if status == 'active':
            check_booking_overlap(
                room, 
                start_time,
                end_time,
                instance=self.instance
            )
            
        return data
    