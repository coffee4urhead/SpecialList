from django.urls import path
from .api import get_or_create_conversation, get_conversation_messages
from .views import ExploreConversationsView, ChatWithUserView

urlpatterns = [
    path('conversations/', ExploreConversationsView.as_view(), name='explore_conversations'),
    path('chat/<int:user_id>/', ChatWithUserView.as_view(), name='chat_with_user'),
    path('api/conversations/', get_or_create_conversation, name='get_or_create_conversation'),
    path('api/messages/', get_conversation_messages, name='get_conversation_messages'),
]
