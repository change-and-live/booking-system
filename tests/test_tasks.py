from django.test import TestCase
from django.core import mail
from django.contrib.auth import get_user_model
from booking_app.models import Room, Booking
from booking_app.tasks import send_booking_notification
from datetime import datetime, timedelta
import pytz
from unittest.mock import patch

User = get_user_model()

class SendBookingNotificationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='Ляляшкин', 
            password='5555',
            email='lyalyashkin@example.com'
        )
        self.room = Room.objects.create(name="Тренинг-зал", capacity=30)
        self.now = datetime.now(pytz.utc)
    
    def create_booking(self, notification_sent=False):
        start = self.now + timedelta(hours=1)
        end = start + timedelta(hours=2)
        return Booking.objects.create(
            room=self.room,
            user=self.user,
            start_time=start,
            end_time=end,
            notification_sent=notification_sent
        )
    
    def test_send_notifications(self):
        booking = self.create_booking()
        
        with self.settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            send_booking_notification()
        
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertEqual(email.subject, f"Подтверждение бронирования: {self.room.name}")
        self.assertIn(f"Здравствуйте, {self.user.username}!", email.body)
        self.assertIn(f"Ваша бронь на комнату {self.room.name} подтверждена", email.body)
        
        booking.refresh_from_db()
        self.assertTrue(booking.notification_sent)
    
    @patch('booking_app.tasks.send_mail')
    @patch('booking_app.tasks.logger')
    def test_email_send_failure(self, mock_logger, mock_send_mail):
        mock_send_mail.side_effect = Exception("Ошибка отправки")
        booking = self.create_booking()
        
        send_booking_notification()
        
        mock_logger.error.assert_called()
        self.assertIn("Ошибка отправки уведомления", mock_logger.error.call_args[0][0])
        
        booking.refresh_from_db()
        self.assertFalse(booking.notification_sent)