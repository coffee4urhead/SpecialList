from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404

from JobJab.core.forms import CleanUserCreationForm, CleanLoginForm
from django.contrib import messages

from JobJab.core.models import CustomUser
from JobJab.reviews.models import Review, ReviewType


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
    reviews = Review.objects.filter(
        review_type=ReviewType.WEBSITE.value
    ).select_related('reviewer').order_by('-created_at')[:4]

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
def account_view(request, username):
    viewed_account = get_object_or_404(CustomUser, username=username)

    is_owner = (request.user == viewed_account)

    context = {
        'viewed_account': viewed_account,
        'is_owner': is_owner,
    }

    if is_owner:
        return render(request, 'core/accounts/my_account.html', context)
    else:
        return render(request, 'core/accounts/public_profile.html', context)