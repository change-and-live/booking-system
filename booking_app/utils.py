from django.core.exceptions import ValidationError
from django.utils import timezone

def validate_booking_times(start_time, end_time):
    if start_time >= end_time:
        raise ValidationError("Время окончания должно быть позже начала")
    
    if start_time < timezone.now():
        raise ValidationError("Нельзя бронировать в прошлом")

def check_booking_overlap(room, start_time, end_time, instance=None):
    from booking_app.models import Booking
    overlapping = Booking.objects.filter(
        room=room,
        status='active',
        start_time__lt=end_time,
        end_time__gt=start_time
    )
    
    if instance:
        overlapping = overlapping.exclude(pk=instance.pk)
    
    if overlapping.exists():
        raise ValidationError("Комната уже забронирована")