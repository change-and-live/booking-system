from celery import shared_task
from django.core.mail import send_mail
from .models import Booking
import logging
from django.conf import settings
from config.settings import DEBUG

logger = logging.getLogger('booking_app.tasks')

@shared_task(bind=True, max_retries=3)
def send_booking_notification(self, booking_id):   
    try:
        booking = Booking.objects.get(id=booking_id)
        if booking.notification_sent:
            return
        subject = f"Подтверждение бронирования: {booking.room.name}"
        message = (
                f"Здравствуйте, {booking.user.username}!\n\n"
                f"Ваша бронь на комнату {booking.room.name} подтверждена.\n"
                f"Время: с {booking.start_time.strftime('%d.%m.%Y %H:%M')} "
                f"по {booking.end_time.strftime('%d.%m.%Y %H:%M')}\n\n"
                "С уважением,\nКоманда бронирования"
        ) 
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [booking.user.email] if booking.user.email else [], 
        )
        booking.notification_sent = True
        booking.save(update_fields=['notification_sent'])
        logger.info(f"Уведомление для брони отправлено {booking.id}")
    except Exception as exc:
        logger.error(f"Ошибка отправки уведомления: {exc}")
        self.retry(exc=exc, countdown=60)    