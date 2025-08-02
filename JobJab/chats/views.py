from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch, Count
from django.utils.decorators import method_decorator
from django.views import View

from JobJab.chats.models import Conversation
from JobJab.core.models import CustomUser, Notification


@method_decorator(login_required(login_url='login'), name='dispatch')
class ExploreConversationsView(View):
    def get(self, request):
        filter_type = request.GET.get('filter', 'seeker')
        unread_count = 0

        if request.user.is_authenticated:
            unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

        other_user_prefetch = Prefetch(
            'participants',
            queryset=request.user.__class__.objects.exclude(id=request.user.id),
            to_attr='other_participants'
        )

        conversations = Conversation.objects.filter(participants=request.user) \
            .prefetch_related(other_user_prefetch) \
            .order_by('-updated_at')

        conversation_data = []
        for conv in conversations:
            other_user = conv.other_participants[0] if conv.other_participants else None
            last_message = conv.get_last_message()

            if not other_user:
                continue

            if other_user.user_type == filter_type:
                conversation_data.append({
                    'id': conv.id,
                    'other_user': other_user,
                    'last_message': last_message,
                    'last_message_time': last_message.timestamp if last_message else None,
                    'user_type': other_user.user_type
                })

        print(conversation_data)
        return render(request, 'explore_conversations.html', {
            'conversation_data': conversation_data,
            'current_filter': filter_type,
            'categories': [
                {'name': 'Service Seekers', 'value': 'seeker'},
                {'name': 'Service Providers', 'value': 'provider'},
            ],
            'unread_count': unread_count,
        })


@method_decorator(login_required(login_url='login'), name='dispatch')
class ChatWithUserView(View):
    def get(self, request, user_id):
        other_user = get_object_or_404(CustomUser, id=user_id)
        unread_count = 0

        if request.user.is_authenticated:
            unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        conversations = Conversation.objects.annotate(num_participants=Count('participants')) \
            .filter(num_participants=2, participants=request.user) \
            .filter(participants=other_user)
        if conversations.exists():
            conversation_with_user = conversations.first()
            created = False
        else:
            conversation_with_user = Conversation.objects.create()
            conversation_with_user.participants.add(request.user, other_user)
            created = True

        print(created)
        context = {
            'conversation_with_user': conversation_with_user,
            'other_user': other_user,
            'unread_count': unread_count,
        }
        return render(request, 'chat.html', context)
