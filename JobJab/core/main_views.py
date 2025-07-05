from django.shortcuts import render
from JobJab.reviews.models import WebsiteReview

def home(request):
    reviews = WebsiteReview.objects.all().order_by('-created_at')[:4]

    return render(request, 'core/home.html', {
        'reviews_from_user_to_the_website': reviews
    })


def about(request):
    return render(request, 'core/about-page/about.html')


def privacy_policy(request):
    return render(request, 'template-components/description-component.html')
