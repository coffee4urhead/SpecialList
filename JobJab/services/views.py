from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from JobJab.services.models import ServiceListing
from .forms import ServiceListingForm
from ..booking.forms import ProviderAvailabilityForm


def explore_services(request):
    if request.method == 'POST':
        service_form = ServiceListingForm(request.POST, request.FILES)
        availability_form = ProviderAvailabilityForm(request.POST)

        if service_form.is_valid() and availability_form.is_valid():
            service = service_form.save(commit=False)
            service.provider = request.user
            service.save()

            availability = availability_form.save(commit=False)
            availability.provider = request.user
            availability.save()

            return redirect('explore_services')
    else:
        service_form = ServiceListingForm()
        availability_form = ProviderAvailabilityForm()

    return render(request, 'explore_services.html', {
        'form': service_form,
        'availability_form': availability_form,
        'services': ServiceListing.objects.all()
    })

@login_required
def delete_service(request, pk):
    service = get_object_or_404(ServiceListing, pk=pk)
    if request.user == service.provider:
        service.delete()
    return redirect('explore_services')
