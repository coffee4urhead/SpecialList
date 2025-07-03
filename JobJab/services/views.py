from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from JobJab.services.forms import ServiceListingForm
from JobJab.services.models import ServiceListing

# Create your views here.
def explore_services(request):
    """ return all service listings available by some filters  """

    if request.method == 'POST':
        form = ServiceListingForm(request.POST, request.FILES)
        if form.is_valid():
            service = form.save(commit=False)
            service.provider = request.user
            service.save()
            return redirect('explore_services')
    else:
        form = ServiceListingForm()
        services = ServiceListing.objects.all()

        return render(request, 'explore_services.html', {'form': form, 'services': services})

@login_required
def delete_service(request, pk):
    service = get_object_or_404(ServiceListing, pk=pk)
    if request.user == service.provider:
        service.delete()
    return redirect('explore_services')
