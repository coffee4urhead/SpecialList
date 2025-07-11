from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import modelformset_factory
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.generic import DetailView

from JobJab.booking.forms import BookingForm, WeeklyTimeSlotForm
from JobJab.booking.models import WeeklyTimeSlot
from JobJab.services.models import ServiceListing


def provider_schedule_api(request, provider_id):
    provider = get_user_model().objects.get(id=provider_id)
    slots = WeeklyTimeSlot.objects.filter(
        availability__provider=provider
    ).select_related('availability')

    data = [{
        'day': WeeklyTimeSlot.DAYS_OF_WEEK[slot.day_of_week],
        'start': slot.start_time.strftime("%H:%M"),
        'end': slot.end_time.strftime("%H:%M"),
        'is_booked': slot.is_booked,
        'booking_id': slot.bookings.first().id if slot.is_booked else None
    } for slot in slots]

    return JsonResponse({'slots': data})


class ServiceBookingView(LoginRequiredMixin, DetailView):
    model = ServiceListing
    template_name = 'services/service_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['booking_form'] = BookingForm(provider=self.object.provider)
        context['time_slots'] = WeeklyTimeSlot.objects.filter(
            availability__provider=self.object.provider,
            is_booked=False
        )
        return context

def get_time_slots(request, service_id):
    service = get_object_or_404(ServiceListing, id=service_id)
    provider = service.provider

    slots = WeeklyTimeSlot.objects.filter(
        availability__provider=provider,
        is_booked=False
    ).order_by('day_of_week', 'start_time')

    data = [{
        'id': slot.id,
        'day': WeeklyTimeSlot.DAYS_OF_WEEK[slot.day_of_week][1],
        'start_time': slot.start_time.strftime('%H:%M'),
        'end_time': slot.end_time.strftime('%H:%M'),
    } for slot in slots]

    return JsonResponse({'slots': data})

@login_required
@require_POST
def create_booking(request):
    form = BookingForm(request.POST, provider=request.user)

    if form.is_valid():
        booking = form.save(commit=False)
        booking.seeker = request.user
        booking.provider = booking.service.provider

        slot = booking.time_slot
        if slot.is_booked:
            return JsonResponse({'error': 'This time slot is already booked.'}, status=400)

        slot.is_booked = True
        slot.save()
        booking.save()

        return JsonResponse({'message': 'Booking created successfully.'})
    else:
        return JsonResponse({'errors': form.errors}, status=400)

def create_availability_view(request):
    WeeklyTimeSlotFormSet = modelformset_factory(
        WeeklyTimeSlot,
        form=WeeklyTimeSlotForm,
        extra=5,
        can_delete=True
    )

    #this is not a post request being made so the formset is empty which causes the empty table
    if request.method == 'POST':
        formset = WeeklyTimeSlotFormSet(request.POST)
        if formset.is_valid():
            formset.save()
    else:
        formset = WeeklyTimeSlotFormSet(queryset=WeeklyTimeSlot.objects.none())

    return render(request, 'services-display.html', {
        'formset': formset,
    })