from django.urls import path
from .api import get_or_create_conversation, get_conversation_messages

urlpatterns = [
    path('api/conversations/', get_or_create_conversation, name='get_or_create_conversation'),
    path('api/messages/', get_conversation_messages, name='get_conversation_messages'),
]
