from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View

from JobJab.core.models import CustomUser, Notification, NotificationType
from JobJab.reviews.forms import UserReviewForm
from JobJab.reviews.models import UserReview


class LeaveUserReviewView(LoginRequiredMixin, View):
    def get(self, request, username):
        reviewee = get_object_or_404(CustomUser, username=username)
        form = UserReviewForm(reviewee=reviewee, reviewer=request.user)
        unread_count = 0

        if request.user.is_authenticated:
            unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

        return render(request, 'template-components/review-form-modal.html', {
            'form': form,
            'reviewee': reviewee,
            'unread_count': unread_count,
        })

    def post(self, request, username):
        reviewee = get_object_or_404(CustomUser, username=username)
        form = UserReviewForm(request.POST, reviewee=reviewee, reviewer=request.user)

        if form.is_valid():
            try:
                form.save()

                Notification.create_notification(
                    user=request.user,
                    title=f"Successfully reviewed {reviewee}",
                    message="Make sure you leave responsible reviews so other can be safe in the community!",
                    notification_type=NotificationType.REPORT
                )

                return JsonResponse({
                    'status': 'success',
                    'message': 'Review submitted successfully'
                })
            except ValidationError as e:
                return JsonResponse({
                    'status': 'error',
                    'errors': {'__all__': list(e.messages)}
                }, status=400)
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'errors': {'__all__': [str(e)]}
                }, status=500)
        else:
            return JsonResponse({
                'status': 'error',
                'errors': form.errors.get_json_data()
            }, status=400)


class EditUserReviewView(LoginRequiredMixin, View):
    def get(self, request, username, review_id):
        review = get_object_or_404(UserReview, id=review_id, reviewer=request.user)
        if review.reviewee.username != username:
            return JsonResponse({'status': 'error', 'message': 'Username mismatch'}, status=403)

        form = UserReviewForm(instance=review, reviewer=request.user, reviewee=review.reviewee)
        return render(request, 'template-components/review-form-modal.html', {
            'form': form,
            'reviewee': review.reviewee,
            'edit': True,
            'review_id': review.id
        })

    def post(self, request, username, review_id):
        review = get_object_or_404(UserReview, id=review_id, reviewer=request.user)
        if review.reviewee.username != username:
            return JsonResponse({'status': 'error', 'message': 'Username mismatch'}, status=403)

        form = UserReviewForm(request.POST, instance=review, reviewer=request.user, reviewee=review.reviewee)
        if form.is_valid():
            review = form.save()

            Notification.create_notification(
                user=request.user,
                title=f"Successfully edited review for {review.reviewee}",
                message="Changing your opinion every now and then can make a difference in someone's career",
                notification_type=NotificationType.INFO
            )

            return JsonResponse({'status': 'success', 'message': 'Review updated successfully'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors.get_json_data()}, status=400)


class DeleteUserReviewView(LoginRequiredMixin, View):
    def post(self, request, username, review_id):
        review = get_object_or_404(UserReview, id=review_id, reviewer=request.user)
        if request.user != review.reviewer:
            return redirect('account_view', username=username)

        reviewee_username = review.reviewee.username

        Notification.create_notification(
            user=request.user,
            title=f"Successfully deleted review for {reviewee_username}",
            message="You deleted a review for the user specified!",
            notification_type=NotificationType.INFO
        )
        review.delete()
        return redirect('account_view', username=reviewee_username)
