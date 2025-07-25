from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.views import View
from JobJab.reviews.forms import WebsiteReviewForm
from JobJab.reviews.models import WebsiteReview


class HomeView(View):
    def get(self, request):
        reviews = WebsiteReview.objects.all().order_by('-created_at')[:4]
        return render(request, 'core/home.html', {
            'reviews_from_user_to_the_website': reviews
        })


class AboutView(View):
    def get(self, request):
        form = WebsiteReviewForm(reviewer=request.user) if request.user.is_authenticated else WebsiteReviewForm()
        return render(request, 'core/about-page/about.html', {'website_review_form': form})

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
