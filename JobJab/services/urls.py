from django.urls import path
from . import views
from ..booking.views import ServiceBookingView

urlpatterns = [
    path('explore/', views.explore_services, name='explore_services'),
    path('<int:pk>/', ServiceBookingView.as_view(), name='service_detail'),
    path('delete/<int:pk>/', views.delete_service, name='delete_service'),
]