from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
router.register(r'rooms', views.RoomViewSet, basename='room')
router.register(r'bookings', views.BookingViewSet, basename='booking')

api_root_view = router.get_api_root_view()
api_root_view.cls.__name__ = "Корень API"
api_root_view.cls.__doc__ = "Основные конечные точки API"
      
urlpatterns = [
    path('free-rooms/', views.FreeRoomsView.as_view(), name='free-rooms'),
    path('', include(router.urls)),
]