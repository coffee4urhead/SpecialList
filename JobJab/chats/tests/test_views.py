from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from ..models import Conversation, Message

User = get_user_model()


class ExploreConversationsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(
            username='user1',
            password='testpasss123',
            user_type='seeker',
            email='userr1@example.com'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            password='testpasss123',
            user_type='provider',
            email='userr2@example.com'
        )
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)
        self.message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="Test message"
        )
        self.url = reverse('explore_conversations')

    def test_view_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_view_with_authenticated_user(self):
        self.client.login(username='user1', password='testpasss123', email='userr1@example.com')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'explore_conversations.html')

    def test_filter_by_user_type(self):
        self.client.login(username='user1', password='testpasss123', email='userr1@example.com')

        response = self.client.get(self.url + '?filter=provider')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['conversation_data']), 1)
        self.assertEqual(response.context['conversation_data'][0]['user_type'], 'provider')

        response = self.client.get(self.url + '?filter=seeker')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['conversation_data']), 0)


class ChatWithUserViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='testpasss123', email='userr1@example.com')
        self.user2 = User.objects.create_user(username='user2', password='testpasss123', email='userr2@example.com')
        self.url = reverse('chat_with_user', args=[self.user2.id])

    def test_view_requires_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_new_conversation_creation(self):
        self.client.login(username='user1', password='testpasss123', email='userr1@example.com')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'chat.html')

        conversation = Conversation.objects.first()
        self.assertEqual(conversation.participants.count(), 2)
        self.assertTrue(conversation.participants.filter(id=self.user1.id).exists())
        self.assertTrue(conversation.participants.filter(id=self.user2.id).exists())

    def test_existing_conversation_retrieval(self):
        conversation = Conversation.objects.create()
        conversation.participants.add(self.user1, self.user2)

        self.client.login(username='user1', password='testpasss123', email='userr1@example.com')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['conversation_with_user'], conversation)