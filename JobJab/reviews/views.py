from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from JobJab.core.models import CustomUser
from JobJab.reviews.forms import UserReviewForm


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