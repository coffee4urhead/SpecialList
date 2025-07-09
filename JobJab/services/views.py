from django.contrib.auth.decorators import login_required
from django.forms import modelformset_factory
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




@login_required
def delete_service(request, pk):
    service = get_object_or_404(ServiceListing, pk=pk)
    if request.user == service.provider:
        service.delete()
    return redirect('explore_services')
