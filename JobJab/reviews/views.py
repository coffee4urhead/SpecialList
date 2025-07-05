from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect

from JobJab.core.models import CustomUser
from JobJab.reviews.forms import UserReviewForm
from JobJab.reviews.models import UserReview


# Create your views here.

@login_required
def leave_user_review(request, username):
    reviewee = get_object_or_404(CustomUser, username=username)

    if request.method == "POST":
        form = UserReviewForm(
            request.POST,
            reviewee=reviewee,
            reviewer=request.user
        )

        if form.is_valid():
            try:
                review = form.save()
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

    form = UserReviewForm(reviewee=reviewee, reviewer=request.user)
    return render(request, 'template-components/review-form-modal.html', {
        'form': form,
        'reviewee': reviewee
    })

@login_required
def edit_user_review(request, username, review_id):
    review = get_object_or_404(UserReview, id=review_id, reviewer=request.user)

    if review.reviewee.username != username:
        return JsonResponse({'status': 'error', 'message': 'Username mismatch'}, status=403)

    if request.method == 'POST':
        form = UserReviewForm(
            request.POST,
            instance=review,
            reviewer=request.user,
            reviewee=review.reviewee
        )
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success', 'message': 'Review updated successfully'})
        else:
            return JsonResponse({'status': 'error', 'errors': form.errors.get_json_data()}, status=400)

    form = UserReviewForm(instance=review, reviewer=request.user, reviewee=review.reviewee)
    return render(request, 'template-components/review-form-modal.html', {
        'form': form,
        'reviewee': review.reviewee,
        'edit': True,
        'review_id': review.id
    })

@login_required(login_url='login')
def delete_user_review(request, username, review_id):
    # Only check that the logged-in user is the reviewer
    review = get_object_or_404(UserReview, id=review_id, reviewer=request.user)

    if request.user == review.reviewer:
        reviewee_username = review.reviewee.username
        review.delete()
        return redirect('account_view', username=reviewee_username)

    return redirect('account_view', username=username)
