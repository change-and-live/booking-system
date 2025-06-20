from django.contrib import admin
from .models import Room, Booking, Facility

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'capacity')
    filter_horizontal = ('facilities',)

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('room', 'user', 'start_time', 'end_time', 'status')
    list_filter = ('status', 'room')
    date_hierarchy = 'start_time'

@admin.register(Facility)
class FacilityAdmin(admin.ModelAdmin):
    list_display = ('name',)