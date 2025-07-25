import json
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from JobJab.core.forms import UserOrganizationFormSet, ProfileEditForm
from JobJab.core.models import UserLocation, CustomUser
from JobJab.reviews.models import UserReview


class AccountView(LoginRequiredMixin, View):
    def get(self, request, username):
        viewed_account = get_object_or_404(CustomUser, username=username)
        is_owner = (request.user == viewed_account)

        form = ProfileEditForm(instance=request.user) if is_owner else None
        formset = UserOrganizationFormSet(instance=request.user) if is_owner else None

        context = {
            'viewed_account': viewed_account,
            'form': form,
            'organization_formset': formset,
            'flagged_services': viewed_account.services_favorites.all(),
            'reviews_given': UserReview.objects.filter(reviewee=viewed_account),
        }
        return render(request, 'core/accounts/my_account.html', context)

    def post(self, request, username):
        viewed_account = get_object_or_404(CustomUser, username=username)
        if request.user != viewed_account:
            return redirect('account_view', username=request.user.username)

        form = ProfileEditForm(request.POST, request.FILES, instance=request.user)
        formset = UserOrganizationFormSet(request.POST, instance=request.user)

        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('account_view', username=request.user.username)
        else:
            messages.error(request, 'Please correct the errors below.')

        context = {
            'viewed_account': viewed_account,
            'form': form,
            'organization_formset': formset,
            'flagged_services': viewed_account.services_favorites.all(),
            'reviews_given': UserReview.objects.filter(reviewee=viewed_account),
        }
        return render(request, 'core/accounts/my_account.html', context)


class FollowersFollowingView(View):
    def get(self, request, username):
        user = get_object_or_404(CustomUser, username=username)
        followers = user.followers.all()
        following = user.following.all()
        followers_locations = UserLocation.objects.filter(user__in=followers)
        following_locations = UserLocation.objects.filter(user__in=following)

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
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
            })

        context = {
            'profile_user': user,
            'followers': followers,
            'followers_locations': followers_locations,
            'following': following,
            'following_locations': following_locations,
        }
        return render(request, 'template-components/follow_modal_content.html', context)


class UpdateFollowersView(LoginRequiredMixin, View):
    def post(self, request, username, followerId):
        if request.headers.get('x-requested-with') != 'XMLHttpRequest':
            return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)

        try:
            data = json.loads(request.body)
            action = data.get('action')
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

        try:
            profile_user = CustomUser.objects.get(username=username)
            follower = CustomUser.objects.get(id=followerId)

            if action == 'follow':
                profile_user.followers.add(follower)
                return JsonResponse({'status': 'success', 'message': 'Now following'})
            elif action == 'unfollow':
                profile_user.followers.remove(follower)
                return JsonResponse({'status': 'success', 'message': 'Unfollowed'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Invalid action'}, status=400)
        except CustomUser.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User does not exist'}, status=400)

        return JsonResponse({'status': 'error', 'message': 'Unhandled error'}, status=400)