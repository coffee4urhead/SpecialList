from datetime import timedelta
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.utils import timezone
from django.contrib import messages

from JobJab.booking.models import Booking
from JobJab.dashboard.views.graphs import GraphGenerator


class BookingInfoView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'template-admin-components/admin_booking_info.html'
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

        bookings = Booking.objects.prefetch_related('seeker', 'provider').all()

        context.update({
            'total_bookings': bookings.count(),
            'bookings': bookings,

            'bookings_graph': GraphGenerator.create_service_trend_graph(bookings, start_date, end_date),
        })
        return context