import json

from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from JobJab.core.forms import CleanUserCreationForm, CleanLoginForm, ProfileEditForm, UserOrganizationFormSet
from django.contrib import messages

from JobJab.core.models import CustomUser, UserLocation
from JobJab.reviews.forms import UserReviewForm
from JobJab.reviews.models import WebsiteReview, UserReview


def register(request):
    if request.method == 'POST':
        form = CleanUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now login.')
            return redirect('login')
    else:
        form = CleanUserCreationForm()

    return render(request, 'core/register.html', {'form': form})

def login(request):
    if request.method == 'POST':
        form = CleanLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')

            user = authenticate(request, username=username, password=password)

            if user is not None:
                auth_login(request, user)
                return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = CleanLoginForm()

    return render(request, 'core/login.html', {'form': form})

def logout(request):
    auth_logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('home')

def home(request):
    reviews = WebsiteReview.objects.all().order_by('-created_at')[:4]

    return render(request, 'core/home.html', {
        'reviews_from_user_to_the_website': reviews
    })

def about(request):
    return render(request, 'core/about-page/about.html')

def privacy_policy(request):
    return render(request, 'template-components/description-component.html')


def followers_following_view(request, username):
    user = get_object_or_404(CustomUser, username=username)

    context = {
        'profile_user': user,
        'followers': user.followers.all(),
        'following': user.following.all(),
    }

    return render(request, 'template-components/follow_modal_content.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def leave_user_review(request, username):
    reviewee = get_object_or_404(CustomUser, username=username)

    if request.method == "POST":
        # Create mutable copy of POST data
        post_data = request.POST.copy()
        if 'reviewer_id' not in post_data:
            post_data['reviewer_id'] = request.user.id

        form = UserReviewForm(post_data, reviewee=reviewee, reviewer=request.user)

        if form.is_valid():
            try:
                review = form.save()
                return JsonResponse({'status': 'success'})
            except ValidationError as e:
                return JsonResponse({
                    'status': 'error',
                    'errors': {'__all__': list(e.messages)}
                }, status=400)
        return JsonResponse({
            'status': 'error',
            'errors': form.errors
        }, status=400)

    # GET request
    form = UserReviewForm(
        initial={
            'reviewee_display': str(reviewee),
            'reviewer_id': request.user.id
        },
        reviewee=reviewee,
        reviewer=request.user
    )
    return render(request, 'template-components/review-form-modal.html', {
        'form': form,
        'reviewee': reviewee
    })

@csrf_exempt
@login_required
def update_geolocation(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            lat = data.get('latitude')
            lng = data.get('longitude')

            UserLocation.objects.update_or_create(
                user=request.user,
                defaults={'latitude': lat, 'longitude': lng}
            )

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
    return JsonResponse({'status': 'error'}, status=405)

@login_required
def account_view(request, username):
    viewed_account = get_object_or_404(CustomUser, username=username)
    reviews_given = UserReview.objects.filter(reviewee=viewed_account)
    is_owner = (request.user == viewed_account)

    if is_owner:
        if request.method == 'POST':
            form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
            formset = UserOrganizationFormSet(request.POST, instance=request.user)

            if form.is_valid() and formset.is_valid():
                form.save()
                formset.save()
                messages.success(request, 'Your profile has been updated.')
                return redirect('account_view', username=request.user.username)
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = ProfileEditForm(instance=request.user)
            formset = UserOrganizationFormSet(instance=request.user)
    else:
        form = None
        formset = None

    context = {
        'viewed_account': viewed_account,
        'form': form,
        'organization_formset': formset,
        'reviews_given': reviews_given,
    }

    print(context)
    return render(request,'core/accounts/my_account.html', context)

