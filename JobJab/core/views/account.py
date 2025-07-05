from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect

from JobJab.core.forms import UserOrganizationFormSet, ProfileEditForm
from JobJab.core.models import UserLocation, CustomUser
from JobJab.reviews.models import UserReview


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
    return render(request, 'core/accounts/my_account.html', context)

def followers_following_view(request, username):
    user = get_object_or_404(CustomUser, username=username)

    followers = user.followers.all()
    following = user.following.all()

    followers_locations = UserLocation.objects.filter(user__in=followers)
    following_locations = UserLocation.objects.filter(user__in=following)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        data = {
            'followers': [
                {
                    'username': loc.user.username,
                    'latitude': float(loc.latitude),
                    'longitude': float(loc.longitude),
                } for loc in followers_locations
            ],
            'following': [
                {
                    'username': loc.user.username,
                    'latitude': float(loc.latitude),
                    'longitude': float(loc.longitude),
                } for loc in following_locations
            ]
        }
        return JsonResponse(data)

    context = {
        'profile_user': user,
        'followers': followers,
        'followers_locations': followers_locations,
        'following': following,
        'following_locations': following_locations,
    }

    return render(request, 'template-components/follow_modal_content.html', context)