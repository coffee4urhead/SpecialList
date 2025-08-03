from datetime import timedelta
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import redirect
from django.views.generic import TemplateView
from django.utils import timezone
from django.contrib import messages

from JobJab.dashboard.views.graphs import GraphGenerator
from JobJab.reviews.models import WebsiteReview, UserReview


class ReviewsInfoView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'template-admin-components/admin_reviews_info.html'
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

        website_reviews = WebsiteReview.objects.prefetch_related('reviewer').all()

        user_reviews = UserReview.objects.select_related('reviewer', 'reviewee').all()

        context.update({
            'total_web_reviews': website_reviews.count(),
            'total_user_reviews': user_reviews.count(),
            'website_reviews': website_reviews,
            'user_reviews': user_reviews,

            'website_reviews_graph': GraphGenerator.create_service_trend_graph(website_reviews, start_date, end_date),
            'user_reviews_graph': GraphGenerator.create_service_trend_graph(user_reviews, start_date, end_date),
        })
        return context