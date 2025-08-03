from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.views.generic import TemplateView

from JobJab.core.models import CustomUser, BlacklistItem, UserBlacklistProfile, \
    BlacklistStatus
from JobJab.reviews.models import UserReview
from JobJab.services.models import Comment, ServiceListing


class AdminDashboardView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'admin_home.html'
    login_url = 'login'
    paginate_by = 5

    def test_func(self):
        return self.request.user.is_staff

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(self.get_login_url())

        messages.error(self.request, "Staff privileges required")
        return redirect(self.get_login_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        disputes = BlacklistItem.objects.all().select_related(
            'reporter', 'moderator', 'content_type'
        )

        paginator = Paginator(disputes, self.paginate_by)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        banned_profiles = UserBlacklistProfile.objects.filter(is_banned=True).select_related('user')
        warned_profiles = UserBlacklistProfile.objects.filter(warning_count__gt=0, is_banned=False).select_related(
            'user')

        user_ct = ContentType.objects.get_for_model(CustomUser)
        service_ct = ContentType.objects.get_for_model(ServiceListing)
        review_ct = ContentType.objects.get_for_model(UserReview)
        comment_ct = ContentType.objects.get_for_model(Comment)

        context.update({
            'disputes': disputes,
            'banned_profiles': banned_profiles,
            'warned_profiles': warned_profiles,
            'page_obj': page_obj,
            'reported_users_count': BlacklistItem.objects.filter(
                content_type=user_ct,
                status=BlacklistStatus.PENDING
            ).count(),
            'reported_services_count': BlacklistItem.objects.filter(
                content_type=service_ct,
                status=BlacklistStatus.PENDING
            ).count(),
            'reported_reviews_count': BlacklistItem.objects.filter(
                content_type=review_ct,
                status=BlacklistStatus.PENDING
            ).count(),
            'reported_comments_count': BlacklistItem.objects.filter(
                content_type=comment_ct,
                status=BlacklistStatus.PENDING
            ).count(),
            'user_ct': user_ct,
            'service_ct': service_ct,
            'review_ct': review_ct,
            'comment_ct': comment_ct,
        })

        return context
