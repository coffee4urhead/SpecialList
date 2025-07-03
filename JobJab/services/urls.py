from django.urls import path
from . import views

urlpatterns = [
    path('explore/', views.explore_services, name='explore_services'),
    path('delete/<int:pk>/', views.delete_service, name='delete_service'),
]