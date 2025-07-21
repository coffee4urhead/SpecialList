from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import Conversation

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