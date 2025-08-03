from datetime import timedelta
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.db.models import Count
from django.db.models.functions import TruncDate
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.utils import timezone
from django.contrib import messages

from JobJab.core.models import Organization, CustomUser, Certificate
from ..graphs import GraphGenerator


class CoreInfoView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'template-admin-components/admin_core_info.html'
    login_url = 'login'

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)
        time_period = f"{start_date.strftime('%b %d')} to {end_date.strftime('%b %d')}"

        registration_data = (
            CustomUser.objects
            .filter(date_joined__range=(start_date, end_date))
            .annotate(date=TruncDate('date_joined'))
            .values('date')
            .annotate(count=Count('id'))
            .order_by('date')
        )

        if not registration_data:
            registration_data = [{'date': start_date.date(), 'count': 0}]

        certificates = Certificate.objects.all()
        cert_graph_html = GraphGenerator.create_certificate_status_graph(certificates)

        context.update({
            'organizations': Organization.objects.annotate(member_count=Count('members')).order_by('-member_count'),
            'total_users': CustomUser.objects.count(),
            'users': CustomUser.objects.all(),
            'total_organizations': Organization.objects.count(),
            'unverified_certs_count': Certificate.objects.filter(is_verified=False).count(),
            'unverified_certs': Certificate.objects.filter(is_verified=False),
            'time_period': time_period,
            'user_registration_graph': GraphGenerator.create_user_registration_graph(
                registration_data,
                time_period
            ),
            'certificate_graph': cert_graph_html,
        })
        return context

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(self.get_login_url())
        messages.error(self.request, "Staff privileges required")
        return redirect(self.get_login_url())