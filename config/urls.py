from django.contrib import admin
from django.urls import path, include
from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('booking_app.urls')),
    path('', RedirectView.as_view(url='/api/', permanent=False)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
]