import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from JobJab.core.models import CustomUser, UserLocation

@csrf_exempt
@login_required
def update_geolocation(request, username):
    if request.user.username != username:
        return JsonResponse({
            'status': 'error',
            'message': 'You can only access your own location'
        }, status=403)

    if request.method == 'GET':
        try:
            user_location = UserLocation.objects.get(user__username=username)
            return JsonResponse({
                'status': 'success',
                'exists': True,
                'latitude': user_location.latitude,
                'longitude': user_location.longitude,
                'username': username
            })
        except UserLocation.DoesNotExist:
            return JsonResponse({
                'status': 'success',
                'exists': False,
                'message': 'Location not found',
                'username': username
            })

    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            lat = data.get('latitude')
            lng = data.get('longitude')

            if not all(isinstance(coord, (int, float)) for coord in [lat, lng]):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Invalid coordinates format'
                }, status=400)

            user_location, created = UserLocation.objects.update_or_create(
                user=request.user,
                defaults={
                    'latitude': lat,
                    'longitude': lng
                }
            )

            return JsonResponse({
                'status': 'success',
                'action': 'created' if created else 'updated',
                'latitude': user_location.latitude,
                'longitude': user_location.longitude,
                'username': username
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON data'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }, status=500)

    return JsonResponse({
        'status': 'error',
        'message': 'Method not allowed'
    }, status=405)


@csrf_exempt
def user_location_with_connections(request, username):
    try:
        target_user = CustomUser.objects.get(username=username)

        if request.method == 'POST' and request.user.is_authenticated:
            if request.user.username != username:
                return JsonResponse({
                    'status': 'error',
                    'message': 'You can only update your own location'
                }, status=403)

            data = json.loads(request.body)
            lat = data.get('latitude')
            lng = data.get('longitude')

            user_location, created = UserLocation.objects.update_or_create(
                user=request.user,
                defaults={'latitude': lat, 'longitude': lng}
            )
        else:
            user_location = UserLocation.objects.get(user__username=username)

        followers = target_user.followers.all()
        following = target_user.following.all()

        followers_locations = UserLocation.objects.filter(user__in=followers)
        following_locations = UserLocation.objects.filter(user__in=following)

        return JsonResponse({
            'status': 'success',
            'user_location': {
                'latitude': user_location.latitude,
                'longitude': user_location.longitude,
                'username': username,
                'profile_picture': target_user.profile_picture.url if target_user.profile_picture else None
            },
            'connections': {
                'followers': [
                    {
                        'username': loc.user.username,
                        'latitude': loc.latitude,
                        'longitude': loc.longitude,
                        'profile_picture': loc.user.profile_picture.url if loc.user.profile_picture else None
                    } for loc in followers_locations
                ],
                'following': [
                    {
                        'username': loc.user.username,
                        'latitude': loc.latitude,
                        'longitude': loc.longitude,
                        'profile_picture': loc.user.profile_picture.url if loc.user.profile_picture else None
                    } for loc in following_locations
                ]
            }
        })

    except UserLocation.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Location not found',
            'requires_location': True
        }, status=404)
    except CustomUser.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'User not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)