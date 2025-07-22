import json

from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
import base64
import uuid

from django.utils import timezone

from JobJab.chats.models import UserStatus, Message, Conversation

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if not self.user.is_authenticated:
            await self.close()
            return

        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.update_user_status(online=True)
        await self.accept()

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': self.user.id,
                'online': True,
            }
        )
        other_status = await self.get_other_user_status()
        if other_status:
            await self.send(text_data=json.dumps({
                'type': 'user_status',
                'user_id': other_status['user_id'],
                'online': other_status['online'],
                'last_seen': other_status['last_seen'],
            }))

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
            await self.update_user_status(online=False)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_status',
                    'user_id': self.user.id,
                    'online': False,
                    'last_seen': str(timezone.now())
                }
            )

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'text_message':
            message = data['message']
            new_message = await self.create_message(message)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'sender_id': self.user.id,
                    'message_id': new_message.id,
                    'timestamp': str(new_message.timestamp)
                }
            )

        elif message_type == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': self.user.id,
                    'typing': data['typing']
                }
            )

        elif message_type == 'read_receipt':
            await self.mark_messages_read(data['message_ids'])
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'read_receipt',
                    'reader_id': self.user.id,
                    'message_ids': data['message_ids']
                }
            )

        elif message_type == 'media_message':
            if data.get('image'):
                image_data = data['image']
                format, imgstr = image_data.split(';base64,')
                ext = format.split('/')[-1]
                image_name = f"{uuid.uuid4()}.{ext}"

                message = await self.create_media_message(
                    image=ContentFile(base64.b64decode(imgstr), name=image_name)
                )

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'media_message',
                        'message_id': message.id,
                        'sender_id': self.user.id,
                        'image_url': message.image.url,
                        'timestamp': str(message.timestamp)
                    }
                )

    @database_sync_to_async
    def get_other_user(self, conversation, current_user_id):
        return conversation.participants.exclude(id=current_user_id).first()

    @database_sync_to_async
    def get_user_status(self, user):
        status, _ = UserStatus.objects.get_or_create(user=user)
        return status

    async def get_other_user_status(self):
        conversation = await database_sync_to_async(Conversation.objects.get)(id=self.conversation_id)
        other_user = await self.get_other_user(conversation, self.user.id)
        if not other_user:
            return None

        status = await self.get_user_status(other_user)
        return {
            'user_id': other_user.id,
            'online': status.online,
            'last_seen': str(status.last_seen) if status.last_seen else None,
        }

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'text_message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'message_id': event['message_id'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def get_username(self, user_id):
        try:
            user = User.objects.get(id=user_id)
            return user.username
        except User.DoesNotExist:
            return "Unknown"

    async def typing_indicator(self, event):
        username = await self.get_username(event['user_id'])
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'typing': event['typing'],
            'username': username
        }))

    async def read_receipt(self, event):
        await self.send(text_data=json.dumps({
            'type': 'read_receipt',
            'reader_id': event['reader_id'],
            'message_ids': event['message_ids']
        }))

    async def user_status(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_status',
            'user_id': event['user_id'],
            'online': event.get('online', False),
            'last_seen': event.get('last_seen')
        }))

    async def media_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'media_message',
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'image_url': event['image_url'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def create_message(self, content):
        conversation = Conversation.objects.get(id=self.conversation_id)
        return Message.objects.create(
            conversation=conversation,
            sender=self.user,
            content=content
        )

    @database_sync_to_async
    def create_media_message(self, image=None, video=None):
        conversation = Conversation.objects.get(id=self.conversation_id)
        return Message.objects.create(
            conversation=conversation,
            sender=self.user,
            image=image,
            video=video
        )

    @database_sync_to_async
    def mark_messages_read(self, message_ids):
        Message.objects.filter(
            id__in=message_ids,
            conversation_id=self.conversation_id
        ).exclude(sender=self.user).update(read=True)

    @database_sync_to_async
    def update_user_status(self, online):
        status, _ = UserStatus.objects.get_or_create(user=self.user)
        status.online = online
        if not online:
            status.last_seen = timezone.now()
        status.save()

    async def send_notification(self, user_id, message):
        await self.channel_layer.group_send(
            f"notifications_{user_id}",
            {
                "type": "notification",
                "message": message
            }
        )
