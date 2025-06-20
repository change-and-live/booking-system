from django.test import TestCase
from django.contrib.auth import get_user_model
from booking_app.models import Room, Facility, Booking
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
import pytz

User = get_user_model()

class FacilityModelTest(TestCase):
    def test_create_facility(self):
        facility = Facility.objects.create(
            name="Проектор",
            description="HD проектор с HDMI входом"
        )
        self.assertEqual(facility.name, "Проектор")
        self.assertEqual(str(facility), "Проектор")
    
    def test_unique_facility_name(self):
        Facility.objects.create(name="Маркерная доска")
        with self.assertRaises(Exception):
            Facility.objects.create(name="Маркерная доска")

class RoomModelTest(TestCase):
    def setUp(self):
        self.projector = Facility.objects.create(name="Проектор")
        self.whiteboard = Facility.objects.create(name="Маркерная доска")
        
    def test_create_room(self):
        room = Room.objects.create(
            name="Конференц-зал",
            capacity=15
        )
        room.facilities.add(self.projector)
        self.assertEqual(str(room), "Конференц-зал (до 15 чел.)")
    
    def test_room_facilities_relationship(self):
        room = Room.objects.create(name="Переговорная", capacity=8)
        room.facilities.add(self.projector, self.whiteboard)
        self.assertEqual(room.facilities.count(), 2)

class BookingModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='Иванов', 
            password='0000',
            email='ivanov@example.com'
        )
        self.room = Room.objects.create(
            name='Большой зал', 
            capacity=20
        )
        self.now = datetime.now(pytz.utc)
        
    def create_booking(self, hours_from_now=1, duration_hours=2, status='active'):
        start = self.now + timedelta(hours=hours_from_now)
        end = start + timedelta(hours=duration_hours)
        return Booking.objects.create(
            room=self.room,
            user=self.user,
            start_time=start,
            end_time=end,
            status=status
        )
    
    def test_valid_booking(self):
        booking = self.create_booking()
        self.assertEqual(booking.room.name, "Большой зал")
        self.assertEqual(booking.user.username, "Иванов")
    
    def test_end_time_before_start_time(self):
        start = self.now + timedelta(hours=2)
        end = start - timedelta(hours=1)
        booking = Booking(
            room=self.room,
            user=self.user,
            start_time=start,
            end_time=end
        )
        with self.assertRaises(ValidationError) as context:
            booking.full_clean()
        self.assertIn("Время окончания должно быть позже времени начала", str(context.exception))
    
    def test_overlapping_bookings(self):
        self.create_booking(1, 2)
        
        booking2 = Booking(
            room=self.room,
            user=self.user,
            start_time=self.now + timedelta(hours=1),
            end_time=self.now + timedelta(hours=3)
        )
        with self.assertRaises(ValidationError) as context:
            booking2.full_clean()
        self.assertIn("Комната уже забронирована на выбранное время", str(context.exception))
    
    def test_cancelled_bookings_dont_cause_overlap(self):
        self.create_booking(1, 2, status='cancelled')
        
        booking = Booking(
            room=self.room,
            user=self.user,
            start_time=self.now + timedelta(hours=1),
            end_time=self.now + timedelta(hours=3)
        )
        try:
            booking.full_clean()
        except ValidationError:
            self.fail("Не должно быть ошибки при наличии только отмененного бронирования")
    
    def test_booking_in_past(self):
        booking = Booking(
            room=self.room,
            user=self.user,
            start_time=self.now - timedelta(hours=2),
            end_time=self.now - timedelta(hours=1)
        )
        with self.assertRaises(ValidationError) as context:
            booking.full_clean()
        self.assertIn("Нельзя забронировать комнату на прошедшее время", str(context.exception))
    
    def test_booking_ordering(self):
        booking3 = self.create_booking(4, 1)
        booking1 = self.create_booking(1, 1)
        booking2 = self.create_booking(2, 1)
        
        bookings = Booking.objects.all()
        self.assertEqual(bookings[0].id, booking3.id)
        self.assertEqual(bookings[1].id, booking2.id)