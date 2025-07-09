from django.urls import path
from . import views
from ..booking.views import ServiceBookingView

urlpatterns = [
    path('explore/', views.explore_services, name='explore_services'),
    path('<int:pk>/', ServiceBookingView.as_view(), name='service_detail'),
    path('<int:service_id>/like/', views.like_service, name='like_service'),
    path('<int:service_id>/likers/', views.get_service_likers, name='get_likers'),
    path('delete/<int:pk>/', views.delete_service, name='delete_service'),
]
