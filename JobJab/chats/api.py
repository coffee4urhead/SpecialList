from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import Conversation, Message

#djangorestframework package should be installed

User = get_user_model()


@api_view(['POST'])
def get_or_create_conversation(request):
    recipient_username = request.data.get('participant')
    recipient = User.objects.get(username=recipient_username)

    conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=recipient
    ).first()

    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, recipient)

    return Response({
        'id': conversation.id,
        'other_user': recipient.username,
        'created_at': conversation.created_at
    })


@api_view(['GET'])
def get_conversation_messages(request):
    conversation_id = request.GET.get('conversation_id')

    # Verify the requesting user is a participant
    try:
        conversation = Conversation.objects.get(
            id=conversation_id,
            participants=request.user
        )
    except Conversation.DoesNotExist:
        return Response(
            {'error': 'Conversation not found or access denied'},
            status=404
        )

    messages = Message.objects.filter(
        conversation_id=conversation_id
    ).order_by('timestamp')

    serialized_messages = []
    for message in messages:
        serialized = {
            'id': message.id,
            'content': message.content,
            'sender_id': message.sender.id,
            'sender_username': message.sender.username,
            'timestamp': message.timestamp.isoformat(),
            'image': message.image.url if message.image else None
        }
        serialized_messages.append(serialized)

    return Response(serialized_messages)