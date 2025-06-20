from django.db import models
from django.contrib.auth import get_user_model
from .utils import validate_booking_times, check_booking_overlap


User = get_user_model()

class Facility(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name = "Название")
    description = models.TextField(blank=True, verbose_name = "Описание")

    class Meta:
        verbose_name = "Удобство"
        verbose_name_plural = "Удобства"

    def __str__(self):
        return self.name

class Room(models.Model):
    name = models.CharField(max_length=100, verbose_name = "Название")
    capacity = models.PositiveIntegerField(verbose_name = "Вместимость")
    facilities = models.ManyToManyField(Facility, blank=True, verbose_name = "Удобства")

    class Meta:
        verbose_name = "Комната"
        verbose_name_plural = "Комнаты"

    def __str__(self):
        return f"{self.name} (до {self.capacity} чел.)"

class Booking(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='bookings', verbose_name = "Комната")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name = "Пользователь")
    start_time = models.DateTimeField(verbose_name = "Начало брони")
    end_time = models.DateTimeField(verbose_name = "Конец брони")
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('cancelled', 'Отменена'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active', verbose_name = "Статус")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name = "Дата создания")
    notification_sent = models.BooleanField(default=False, verbose_name = "Статус уведомления")

    class Meta:
        verbose_name = "Бронирование"
        verbose_name_plural = "Бронирования"
        ordering = ['-start_time']
        indexes = [
            models.Index(fields=['start_time', 'end_time']),
        ]

    def __str__(self):
        return f"{self.room.name} - {self.user.username} (с {self.start_time} до {self.end_time})"

    def clean(self):
        validate_booking_times(self.start_time, self.end_time)
        if self.status == 'active':
            check_booking_overlap(
                room=self.room,
                start_time=self.start_time,
                end_time=self.end_time,
                instance=self
            )

