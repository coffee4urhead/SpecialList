from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect

from JobJab.reviews.forms import WebsiteReviewForm
from JobJab.reviews.models import WebsiteReview

def home(request):
    reviews = WebsiteReview.objects.all().order_by('-created_at')[:4]

    return render(request, 'core/home.html', {
        'reviews_from_user_to_the_website': reviews
    })

def about(request):
    if request.method == 'POST' and request.user.is_authenticated:
        website_review_form = WebsiteReviewForm(request.POST, reviewer=request.user)

        if website_review_form.is_valid():
            try:
                website_review_form.save()
                messages.success(request, "Thank you for your review!")
                return redirect('about')
            except ValidationError as e:
                messages.error(request, str(e))
    else:
        website_review_form = WebsiteReviewForm()

    return render(request, 'core/about-page/about.html', {'website_review_form': website_review_form})


def privacy_policy(request):
    return render(request, 'template-components/description-component.html')
