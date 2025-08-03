from datetime import timedelta
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.utils import timezone
from django.contrib import messages
from JobJab.dashboard.views.graphs import GraphGenerator
from JobJab.services.models import ServiceListing, Availability, Comment


class ServicesInfoView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'template-admin-components/admin_services_info.html'
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

        services = ServiceListing.objects.select_related('provider').all()
        recent_services = services.filter(created_at__range=(start_date, end_date))
        availabilities = Availability.objects.all()
        comments = Comment.objects.select_related('author').all()

        context.update({
            'total_services': services.count(),
            'recent_services': recent_services,
            'availabilities': availabilities,
            'comments': comments,
            'services': services,

            'service_graph': GraphGenerator.create_service_trend_graph(services, start_date, end_date),
            'availability_graph': GraphGenerator.create_availability_status_graph(availabilities),
            'comment_graph': GraphGenerator.create_comment_activity_graph(comments, start_date, end_date),
        })
        return context
