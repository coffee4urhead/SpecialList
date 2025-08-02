from django.urls import path
from .api import get_or_create_conversation, get_conversation_messages, get_conversation_images, get_chat_style, \
    update_chat_style
from .views import ExploreConversationsView, ChatWithUserView

urlpatterns = [
    path('conversations/', ExploreConversationsView.as_view(), name='explore_conversations'),
    path('chat/<int:user_id>/', ChatWithUserView.as_view(), name='chat_with_user'),
    path('api/conversations/', get_or_create_conversation, name='get_or_create_conversation'),
    path('api/messages/', get_conversation_messages, name='get_conversation_messages'),
    path('api/images/', get_conversation_images, name='get_conversation_images'),
    path('api/chat-style/', get_chat_style, name='get_chat_style'),
    path('api/chat-style/update/', update_chat_style, name='update_chat_style'),
]
