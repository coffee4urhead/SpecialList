import json
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from JobJab.core.models import CustomUser, UserLocation, Notification, NotificationType


@method_decorator(csrf_exempt, name='dispatch')
class UpdateGeolocationView(LoginRequiredMixin, View):
    def dispatch(self, request, *args, **kwargs):
        if request.user.username != kwargs['username']:
            return JsonResponse({'status': 'error', 'message': 'You can only access your own location'}, status=403)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, username):
        try:
            loc = UserLocation.objects.get(user__username=username)
            return JsonResponse({
                'status': 'success', 'exists': True,
                'latitude': loc.latitude, 'longitude': loc.longitude, 'username': username
            })
        except UserLocation.DoesNotExist:
            return JsonResponse(
                {'status': 'success', 'exists': False, 'message': 'Location not found', 'username': username})

    def post(self, request, username):
        try:
            data = json.loads(request.body)
            lat, lng = data.get('latitude'), data.get('longitude')
            if not all(isinstance(c, (int, float)) for c in [lat, lng]):
                return JsonResponse({'status': 'error', 'message': 'Invalid coordinates format'}, status=400)

            location, created = UserLocation.objects.update_or_create(
                user=request.user, defaults={'latitude': lat, 'longitude': lng})

            Notification.create_notification(
                user=request.user,
                title=f"Successfully attached location to user {username}",
                message="Your location is now visible and your followers can see you as well as those you follow!",
                notification_type=NotificationType.INFO
            )

            return JsonResponse({
                'status': 'success', 'action': 'created' if created else 'updated',
                'latitude': location.latitude, 'longitude': location.longitude, 'username': username
            })
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@method_decorator(csrf_exempt, name='dispatch')
class UserLocationWithConnectionsView(View):
    def post(self, request, username):
        return self.handle(request, username)

    def get(self, request, username):
        return self.handle(request, username)

    def handle(self, request, username):
        try:
            user = CustomUser.objects.get(username=username)
            if request.method == 'POST' and request.user.is_authenticated and request.user.username == username:
                data = json.loads(request.body)
                UserLocation.objects.update_or_create(
                    user=request.user, defaults={'latitude': data.get('latitude'), 'longitude': data.get('longitude')})

            user_location = UserLocation.objects.get(user__username=username)
            followers = user.followers.all()
            following = user.following.all()

            followers_data = [
                {'username': loc.user.username, 'latitude': loc.latitude, 'longitude': loc.longitude,
                 'profile_picture': loc.user.profile_picture.url if loc.user.profile_picture else None}
                for loc in UserLocation.objects.filter(user__in=followers)]

            following_data = [
                {'username': loc.user.username, 'latitude': loc.latitude, 'longitude': loc.longitude,
                 'profile_picture': loc.user.profile_picture.url if loc.user.profile_picture else None}
                for loc in UserLocation.objects.filter(user__in=following)]

            return JsonResponse({
                'status': 'success',
                'user_location': {
                    'latitude': user_location.latitude,
                    'longitude': user_location.longitude,
                    'username': username,
                    'profile_picture': user.profile_picture.url if user.profile_picture else None
                },
                'connections': {
                    'followers': followers_data,
                    'following': following_data
                }
            })

        except UserLocation.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Location not found', 'requires_location': True},
                                status=404)
        except CustomUser.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'User not found'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
