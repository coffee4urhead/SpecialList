from django.shortcuts import render, redirect
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
            return redirect('service_list')
    else:
        form = ServiceListingForm()
        services = ServiceListing.objects.all()

        return render(request, 'explore_services.html', {'form': form, 'services': services})