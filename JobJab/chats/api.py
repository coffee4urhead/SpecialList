from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import Conversation, Message

# djangorestframework package should be installed

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


@api_view(['GET'])
def get_conversation_images(request):
    conversation_id = request.GET.get('conversation_id')

    if not conversation_id:
        return Response({'error': 'conversation_id parameter is required'}, status=400)

    try:
        conversation_id = int(str(conversation_id).rstrip('/'))
    except (ValueError, TypeError):
        return Response(
            {'error': 'Invalid conversation_id format. Must be a number.'},
            status=400
        )

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

    messages_with_images = Message.objects.filter(
        conversation_id=conversation_id,
        image__isnull=False
    ).exclude(image='').order_by('-timestamp')

    images = []
    for message in messages_with_images:
        try:
            if message.image:
                images.append({
                    'id': message.id,
                    'image_url': message.image.url,
                    'sender': message.sender.username,
                    'timestamp': message.timestamp.isoformat(),
                    'caption': message.content
                })
        except ValueError:
            continue

    return Response({'images': images})


@api_view(['GET'])
def get_chat_style(request):
    user = request.user
    return Response({
        'bubble_color': user.chat_bubble_color,
        'bubble_shape': user.chat_bubble_shape,
    })


@api_view(['POST'])
def update_chat_style(request):
    user = request.user
    bubble_color = request.data.get('bubble_color', '#32AE88')
    bubble_shape = request.data.get('bubble_shape', 'rounded')

    user.chat_bubble_color = bubble_color
    user.chat_bubble_shape = bubble_shape
    user.save()

    return Response({'success': True})
