from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View

from JobJab.core.models import CustomUser, Notification
from JobJab.reviews.forms import WebsiteReviewForm
from JobJab.reviews.models import WebsiteReview


class HomeView(View):
    def get(self, request):
        reviews = WebsiteReview.objects.filter(is_active=True).order_by('-created_at')[:4]
        unread_count = 0

        if request.user.is_authenticated:
            unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        return render(request, 'core/home.html', {
            'reviews_from_user_to_the_website': reviews,
            'unread_count': unread_count,
        })


class AboutView(View):
    def get(self, request):
        unread_count = 0

        if request.user.is_authenticated:
            unread_count = Notification.objects.filter(user=request.user, is_read=False).count()
        form = WebsiteReviewForm(reviewer=request.user) if request.user.is_authenticated else WebsiteReviewForm()
        return render(request, 'core/about-page/about.html', {'website_review_form': form, 'unread_count': unread_count,})

    def post(self, request):
        if not request.user.is_authenticated:
            return redirect('login')

        form = WebsiteReviewForm(request.POST, reviewer=request.user)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Thank you for your review!")
                return redirect('about')
            except ValidationError as e:
                messages.error(request, str(e))

        return render(request, 'core/about-page/about.html', {'website_review_form': form})


class PrivacyPolicyView(View):
    def get(self, request):
        return render(request, 'template-components/description-component.html')

class NotificationView(View):
    login_url = 'login'
    template_name = 'core/notification-page.html'

    def get(self, request, username):
        user_account = get_object_or_404(CustomUser, username=username)

        notifications = user_account.notifications.all()

        unread_notifications = notifications.filter(is_read=False)
        unread_notifications.update(is_read=True)

        unread_count = user_account.notifications.filter(is_read=False).count()

        context = {
            'account': user_account,
            'notifications': notifications,
            'unread_count': unread_count,
            'total_count': notifications.count(),
        }
        return render(request, self.template_name, context)

class MarkNotificationAsReadView(LoginRequiredMixin, View):
    def post(self, request, pk):
        notification = get_object_or_404(Notification, pk=pk, user=request.user)
        notification.mark_as_read()
        return JsonResponse({'status': 'success'})