from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from booking_app.models import Room, Facility, Booking
from datetime import datetime, timedelta
import pytz

User = get_user_model()

class RoomViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='Петров', 
            password='1111'
        )
        self.projector = Facility.objects.create(name="Проектор")
        self.whiteboard = Facility.objects.create(name="Маркерная доска")
        
        self.room1 = Room.objects.create(name="Малая переговорка", capacity=4)
        self.room2 = Room.objects.create(name="Конференц-зал", capacity=15)
        self.room2.facilities.add(self.projector)
    
    def test_filter_by_capacity(self):
        response = self.client.get('/api/rooms/?capacity=10')
        self.assertEqual(response.data[0]['name'], "Конференц-зал")
    
    def test_filter_by_facilities(self):
        response = self.client.get(f'/api/rooms/?facilities={self.projector.id}')
        self.assertEqual(response.data[0]['name'], "Конференц-зал")

class FreeRoomsViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='Сидоров', 
            password='2222'
        )
        self.client.force_authenticate(user=self.user)
        
        self.room1 = Room.objects.create(name="Зал 1", capacity=8)
        self.room2 = Room.objects.create(name="Зал 2", capacity=12)
        
        self.now = datetime.now(pytz.utc)
        
    def create_booking(self, room, hours_from_now, duration_hours):
        start = self.now + timedelta(hours=hours_from_now)
        end = start + timedelta(hours=duration_hours)
        return Booking.objects.create(
            room=room,
            user=self.user,
            start_time=start,
            end_time=end
        )
    
    def test_free_rooms_no_bookings(self):
        start = self.now + timedelta(hours=1)
        end = start + timedelta(hours=2)
        
        response = self.client.get(
            '/api/free-rooms/',
            {'start_time': start.isoformat(), 'end_time': end.isoformat()}
        )
        self.assertEqual(len(response.data), 2)
    
    def test_free_rooms_with_bookings(self):
        self.create_booking(self.room1, 1, 2)
        
        start = self.now + timedelta(hours=1)
        end = start + timedelta(hours=2)
        
        response = self.client.get(
            '/api/free-rooms/',
            {'start_time': start.isoformat(), 'end_time': end.isoformat()}
        )
        self.assertEqual(response.data[0]['name'], "Зал 2")

class BookingViewSetTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='Бабаев', 
            password='3333',
            email='babaev@example.com'
        )
        self.client.force_authenticate(user=self.user)
        
        self.room = Room.objects.create(name="Зал заседаний", capacity=25)
        self.now = datetime.now(pytz.utc)
    
    def test_create_booking(self):
        start = self.now + timedelta(hours=1)
        end = start + timedelta(hours=2)
        
        data = {
            'room_id': self.room.id,
            'start_time': start.isoformat(),
            'end_time': end.isoformat()
        }
        
        response = self.client.post('/api/bookings/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['room']['name'], "Зал заседаний")
    
    def test_create_overlapping_booking(self):
        Booking.objects.create(
            room=self.room,
            user=self.user,
            start_time=self.now + timedelta(hours=1),
            end_time=self.now + timedelta(hours=2)
        )
        
        data = {
            'room_id': self.room.id,
            'start_time': (self.now + timedelta(hours=1.5)).isoformat(),
            'end_time': (self.now + timedelta(hours=3)).isoformat()
        }
        
        response = self.client.post('/api/bookings/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Комната уже забронирована", str(response.data))
    
    def test_cancel_booking(self):
        booking = Booking.objects.create(
            room=self.room,
            user=self.user,
            start_time=self.now + timedelta(hours=1),
            end_time=self.now + timedelta(hours=2)
        )
        
        response = self.client.delete(f'/api/bookings/{booking.id}/')
        booking.refresh_from_db()
        self.assertEqual(booking.status, 'cancelled')
    
    def test_user_cannot_cancel_others_booking(self):
        other_user = User.objects.create_user(
            username='Капустин', 
            password='4444'
        )
        booking = Booking.objects.create(
            room=self.room,
            user=other_user,
            start_time=self.now + timedelta(hours=1),
            end_time=self.now + timedelta(hours=2)
        )
        
        response = self.client.delete(f'/api/bookings/{booking.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)