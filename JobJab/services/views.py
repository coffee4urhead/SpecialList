from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from JobJab.services.models import ServiceListing, Availability
from .forms import ServiceListingForm, AvailabilityForm
from ..booking.forms import ProviderAvailabilityForm
from ..booking.models import ProviderAvailability, WeeklyTimeSlot

DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

@login_required
def explore_services(request):
    availability, _ = ProviderAvailability.objects.get_or_create(provider=request.user)

    if request.method == 'POST':
        form = ProviderAvailabilityForm(request.POST, instance=availability)
        if form.is_valid():
            form.save()

            availability.time_slots.all().delete()
            availability._generate_weekly_slots()

            return redirect('explore_services')
    else:
        form = ProviderAvailabilityForm(instance=availability)

    time_slots = availability.time_slots.order_by('day_of_week', 'start_time')

    return render(request, 'explore_services.html', {
        'form': ServiceListingForm(),
        'availability_form': form,
        'time_slots': time_slots,
        'services': ServiceListing.objects.all()
    })


@login_required(login_url='login')
def like_service(request, service_id):
    service = get_object_or_404(ServiceListing, id=service_id)
    user = request.user

    if request.method == 'POST':
        if user in service.likes.all():
            service.likes.remove(user)
            liked = False
        else:
            service.likes.add(user)
            liked = True

        return JsonResponse({
            'liked': liked,
            'like_count': service.likes.count()
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required(login_url='login')
def flag_favourite(request, service_id):
    service = get_object_or_404(ServiceListing, id=service_id)
    user = request.user

    if request.method == 'POST':
        if user in service.favorite_flagged.all():
            service.favorite_flagged.remove(user)
            flagged = False
        else:
            service.favorite_flagged.add(user)
            flagged = True

        return JsonResponse({
            'flagged': flagged,
            'flagged_count': service.favorite_flagged.count()
        })

    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def get_service_likers(request, service_id):
    service = get_object_or_404(ServiceListing, id=service_id)
    likers = service.likes.all()

    data = {
        "likers": [
            {
                "username": user.username,
                "full_name": user.get_full_name(),
                'joined_on': user.date_joined.strftime('%B %d, %Y'),
                "profile_pic": user.profile_picture.url if user.profile_picture else None,
            } for user in likers
        ]
    }
    return JsonResponse(data)

@login_required
def delete_service(request, pk):
    service = get_object_or_404(ServiceListing, pk=pk)
    if request.user == service.provider:
        service.delete()
    return redirect('explore_services')
