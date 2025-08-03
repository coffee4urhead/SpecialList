from datetime import timedelta
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.utils import timezone
from django.contrib import messages

from JobJab.chats.models import Conversation, Message
from JobJab.dashboard.views.graphs import GraphGenerator


class ChatsInfoView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'template-admin-components/admin_chats_info.html'
    login_url = 'login'

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(self.get_login_url())
        messages.error(self.request, "Staff privileges required")
        return redirect(self.get_login_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=30)

        chats = Conversation.objects.prefetch_related('participants').all()
        recent_chats = chats.filter(created_at__range=(start_date, end_date))
        messages = Message.objects.select_related('sender').all()
        messages_count = messages.count()

        context.update({
            'total_chats': chats.count(),
            'total_messages': messages_count,
            'messages': messages,
            'recent_chats': recent_chats,
            'chats': chats,

            'messages_graph': GraphGenerator.create_service_trend_graph(messages, start_date, end_date,
                                                                    arg_getter='timestamp'),
            'chats_graph': GraphGenerator.create_service_trend_graph(chats, start_date, end_date),
        })
        return context