from channels.testing import WebsocketCommunicator
from django.contrib.auth import get_user_model
from django.test import TestCase
from ..consumers import ChatConsumer
from ..models import Conversation, UserStatus, Message
from channels.db import database_sync_to_async
from django.utils import timezone
import json

User = get_user_model()


class ChatConsumerTest(TestCase):
    async def asyncSetUp(self):
        # Create test users
        self.user1 = await database_sync_to_async(User.objects.create_user)(
            username='testuser1',
            password='testpass123',
            email='user1@example.com'
        )
        self.user2 = await database_sync_to_async(User.objects.create_user)(
            username='testuser2',
            password='testpass123',
            email='user2@example.com'
        )

        # Create conversation
        self.conversation = await database_sync_to_async(Conversation.objects.create)()
        await database_sync_to_async(self.conversation.participants.add)(self.user1, self.user2)

        # Set attributes that the consumer expects
        self.conversation_id = str(self.conversation.id)
        self.room_group_name = f'chat_{self.conversation_id}'

        # Create initial user status
        await database_sync_to_async(UserStatus.objects.create)(
            user=self.user1,
            online=False
        )
        await database_sync_to_async(UserStatus.objects.create)(
            user=self.user2,
            online=False
        )

    async def asyncTearDown(self):
        # Clean up database
        await database_sync_to_async(Message.objects.all().delete)()
        await database_sync_to_async(UserStatus.objects.all().delete)()
        await database_sync_to_async(self.conversation.delete)()
        await database_sync_to_async(self.user1.delete)()
        await database_sync_to_async(self.user2.delete)()

    def get_communicator(self, user):
        """Helper to create a communicator with proper scope"""
        communicator = WebsocketCommunicator(
            ChatConsumer.as_asgi(),
            f"/ws/chat/{self.conversation_id}/"
        )
        communicator.scope = {
            'type': 'websocket',
            'user': user,
            'url_route': {
                'kwargs': {'conversation_id': self.conversation_id}
            }
        }
        return communicator

    async def test_connect_and_disconnect(self):
        communicator = self.get_communicator(self.user1)

        # Test connection
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Verify user status was updated
        status = await database_sync_to_async(UserStatus.objects.get)(user=self.user1)
        self.assertTrue(status.online)

        # Test disconnect
        await communicator.disconnect()
        status = await database_sync_to_async(UserStatus.objects.get)(user=self.user1)
        self.assertFalse(status.online)

    async def test_receive_text_message(self):
        communicator = self.get_communicator(self.user1)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Send a text message
        await communicator.send_json_to({
            'type': 'text_message',
            'message': 'Hello world'
        })

        # Receive the echoed message
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'chat_message')
        self.assertEqual(response['message'], 'Hello world')
        self.assertEqual(response['sender_id'], self.user1.id)

        # Verify message was created in database
        message_count = await database_sync_to_async(Message.objects.count)()
        self.assertEqual(message_count, 1)

        await communicator.disconnect()

    async def test_typing_indicator(self):
        communicator = self.get_communicator(self.user1)
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Send typing indicator
        await communicator.send_json_to({
            'type': 'typing',
            'typing': True
        })

        # Receive the typing indicator
        response = await communicator.receive_json_from()
        self.assertEqual(response['type'], 'typing')
        self.assertEqual(response['user_id'], self.user1.id)
        self.assertTrue(response['typing'])

        await communicator.disconnect()

    async def test_user_status_notification(self):
        # First user connects
        communicator1 = self.get_communicator(self.user1)
        connected, _ = await communicator1.connect()
        self.assertTrue(connected)

        # Second user connects
        communicator2 = self.get_communicator(self.user2)
        connected, _ = await communicator2.connect()
        self.assertTrue(connected)

        # Second user should receive status update about first user
        response = await communicator2.receive_json_from()
        self.assertEqual(response['type'], 'user_status')
        self.assertEqual(response['user_id'], self.user1.id)
        self.assertTrue(response['online'])

        # First user should receive status update about second user
        response = await communicator1.receive_json_from()
        self.assertEqual(response['type'], 'user_status')
        self.assertEqual(response['user_id'], self.user2.id)
        self.assertTrue(response['online'])

        # Disconnect first user
        await communicator1.disconnect()

        # Second user should receive disconnect notification
        response = await communicator2.receive_json_from()
        self.assertEqual(response['type'], 'user_status')
        self.assertEqual(response['user_id'], self.user1.id)
        self.assertFalse(response['online'])

        await communicator2.disconnect()
