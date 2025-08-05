from django.test import TestCase
from django.contrib.auth import get_user_model
from JobJab.chats.models import Conversation, Message, UserStatus
from django.utils import timezone

User = get_user_model()


class ConversationModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='testpasss123', email='userr1@example.com')
        self.user2 = User.objects.create_user(username='user2', password='testpasss123', email='userr2@example.com')
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user1, self.user2)

    def test_conversation_creation(self):
        self.assertEqual(self.conversation.participants.count(), 2)
        self.assertTrue(self.conversation.participants.filter(username='user1').exists())
        self.assertTrue(self.conversation.participants.filter(username='user2').exists())

    def test_get_last_message(self):
        message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user1,
            content="Test message"
        )
        last_message = self.conversation.get_last_message()
        self.assertEqual(last_message, message)


class MessageModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.conversation = Conversation.objects.create()
        self.conversation.participants.add(self.user)
        self.message = Message.objects.create(
            conversation=self.conversation,
            sender=self.user,
            content="Test message"
        )

    def test_message_creation(self):
        self.assertEqual(self.message.content, "Test message")
        self.assertEqual(self.message.sender.username, "testuser")
        self.assertFalse(self.message.read)
        self.assertIsNotNone(self.message.timestamp)


class UserStatusModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.status = UserStatus.objects.create(user=self.user, online=True)

    def test_status_creation(self):
        self.assertTrue(self.status.online)
        self.assertIsNotNone(self.status.last_seen)

    def test_status_str(self):
        self.assertEqual(str(self.status), f"{self.user.username} - {'Online' if self.status.online else 'Offline'}")