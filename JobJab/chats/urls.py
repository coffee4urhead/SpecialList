from django.urls import path
from .api import get_or_create_conversation, get_conversation_messages
from .views import explore_conversations, chat_with_user

urlpatterns = [
    path('conversations/', explore_conversations, name='explore_conversations'),
    path('chat/<int:user_id>/', chat_with_user, name='chat_with_user'),
    path('api/conversations/', get_or_create_conversation, name='get_or_create_conversation'),
    path('api/messages/', get_conversation_messages, name='get_conversation_messages'),
]
