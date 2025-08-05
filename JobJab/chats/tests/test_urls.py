from django.test import TestCase
from django.urls import reverse, resolve
from ..views import ExploreConversationsView, ChatWithUserView

class UrlsTest(TestCase):
    def test_explore_conversations_url(self):
        url = reverse('explore_conversations')
        self.assertEqual(resolve(url).func.view_class, ExploreConversationsView)

    def test_chat_with_user_url(self):
        url = reverse('chat_with_user', args=[1])
        self.assertEqual(resolve(url).func.view_class, ChatWithUserView)