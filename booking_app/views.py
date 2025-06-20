from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.exceptions import ValidationError
from .models import Room, Booking
from .serializers import RoomSerializer, BookingSerializer
from django.utils.dateparse import parse_datetime
from .tasks import send_booking_notification

class RoomViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RoomSerializer
    permission_classes = [AllowAny] # [IsAuthenticated]

    def get_view_name(self):
        try:
            if self.action == 'retrieve':
                return "Детали комнаты"
            return "Список комнат"
        except AttributeError:
            return "Комнаты"
    
    def get_queryset(self):
        queryset = Room.objects.all()
        
        capacity = self.request.query_params.get('capacity')
        if capacity:
            try:
                capacity = int(capacity)
                queryset = queryset.filter(capacity__gte=capacity)
            except ValueError:
                raise ValidationError("Вместимость должна быть числом")
            
        facilities = self.request.query_params.getlist('facilities')
        if facilities:
            try:
                facility_ids = [int(fid) for fid in facilities]
                for fid in facility_ids:
                    queryset = queryset.filter(facilities__id=fid)
            except ValueError:
                raise ValidationError("ID удобств должны быть числами")

        return queryset

class FreeRoomsView(generics.ListAPIView):
    serializer_class = RoomSerializer
    permission_classes = [IsAuthenticated]

    def get_view_name(self):
        try:
            return "Список свободных комнат"
        except AttributeError:
            return "Свободные комнаты"
        
    def get_queryset(self):
        start_dt = self.request.query_params.get('start_time')
        end_dt = self.request.query_params.get('end_time')
        start_time = parse_datetime(start_dt)
        end_time = parse_datetime(end_dt)
        
        if not start_time or not end_time:
            raise ValidationError("Требуются start_time и end_time")
        
        if start_time >= end_time:
            raise ValidationError("Конец должен быть позже начала")

        booked_rooms = Booking.objects.filter(
            status='active', 
            start_time__lt=end_time,
            end_time__gt=start_time
        ).values_list('room_id', flat=True)
                
        rooms = Room.objects.exclude(id__in=booked_rooms)
        return rooms
    
class BookingViewSet(viewsets.ModelViewSet):
    serializer_class = BookingSerializer
    permission_classes =  [IsAuthenticated]

    def get_view_name(self):
        try:
            if self.action == 'retrieve':
                return "Детали бронирования"
            return "Список бронирований"
        except AttributeError:
            return "Бронирования"

    def get_queryset(self):
        queryset = Booking.objects.filter(user=self.request.user)
        
        status_param = self.request.query_params.get('status')
        
        if status_param == 'all':
            return queryset
        elif status_param:
            return queryset.filter(status=status_param)
        else:
            return queryset.filter(status='active')
            
    def perform_create(self, serializer):
        booking = serializer.save(user=self.request.user)
        try:
            send_booking_notification(booking.id)
        except Exception as e:
            print(f"Ошибка отправки уведомления: {e}")
    
    def destroy(self, requeat, *args, **kwargs):
        instance = self.get_object()
        instance.status = 'cancelled'
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    