from datetime import timedelta
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.utils import timezone
from django.contrib import messages

from JobJab.dashboard.views.graphs import GraphGenerator
from JobJab.subscriptions.models import SubscriptionRecord


class SubscriptionsInfoView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'template-admin-components/admin_subscriptions_info.html'
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

        subscriptions = SubscriptionRecord.objects.select_related('user').all()
        recent_subscriptions = subscriptions.filter(created_at__range=(start_date, end_date))

        context.update({
            'total_subscriptions': subscriptions.count(),
            'recent_subscriptions': recent_subscriptions,
            'subscriptions': subscriptions,

            'subscriptions_graph': GraphGenerator.create_service_trend_graph(subscriptions, start_date, end_date),
        })
        return context