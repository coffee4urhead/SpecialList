from django.urls import path, include
from . import views

urlpatterns = [
    path('explore/', views.explore_services, name='explore_services'),
]