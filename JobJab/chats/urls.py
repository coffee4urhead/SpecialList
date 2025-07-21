from django.urls import path
from .api import get_or_create_conversation

urlpatterns = [
    path('api/conversations/', get_or_create_conversation, name='get_or_create_conversation'),
]