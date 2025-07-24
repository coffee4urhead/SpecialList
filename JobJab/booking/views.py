from decimal import Decimal

import stripe
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import modelformset_factory
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.views.generic import DetailView

from JobJab import settings
from JobJab.booking.forms import BookingForm, WeeklyTimeSlotForm
from JobJab.booking.models import WeeklyTimeSlot, Booking
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


def create_booking(request):
    if request.method == 'POST':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.seeker = request.user
            booking.price = booking.calculate_price()
            booking.save()

            booking.time_slot.is_booked = True
            booking.time_slot.save()

            return JsonResponse({
                'success': True,
                'booking_id': booking.id,
                'amount': float(booking.price),
            })
    return JsonResponse({'error': 'Invalid request'}, status=400)

def create_availability_view(request):
    WeeklyTimeSlotFormSet = modelformset_factory(
        WeeklyTimeSlot,
        form=WeeklyTimeSlotForm,
        extra=5,
        can_delete=True
    )

    if request.method == 'POST':
        formset = WeeklyTimeSlotFormSet(request.POST)
        if formset.is_valid():
            formset.save()
    else:
        formset = WeeklyTimeSlotFormSet(queryset=WeeklyTimeSlot.objects.none())

    return render(request, 'services-display.html', {
        'formset': formset,
    })

from collections import defaultdict

@login_required(login_url='login')
def availability_table_view(request):
    time_slots = WeeklyTimeSlot.objects.filter(
        availability__provider=request.user
    ).order_by('day_of_week', 'start_time')

    slots_by_day = defaultdict(list)
    for slot in time_slots:
        slots_by_day[slot.day_of_week].append(slot)

    days = [(0, "Monday"), (1, "Tuesday"), (2, "Wednesday"), (3, "Thursday"), (4, "Friday")]

    unique_times = sorted({
        (slot.start_time, slot.end_time)
        for slot in time_slots
    })

    return render(request, 'partials/_availability_table.html', {
        'slots_by_day': slots_by_day,
        'days': days,
        'time_ranges': unique_times,
    })


stripe.api_key = settings.STRIPE_SECRET_KEY

@csrf_exempt
def create_payment_intent(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, seeker=request.user)

    try:
        amount = int(booking.calculate_price() * 100)

        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            metadata={
                'booking_id': booking.id,
                'user_id': request.user.id
            },
        )

        return JsonResponse({
            'clientSecret': intent['client_secret'],
            'amount': amount,
            'booking_id': booking.id,
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=403)

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)

    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        booking_id = payment_intent['metadata']['booking_id']

        try:
            booking = Booking.objects.get(id=booking_id)
            booking.payment_status = 'paid'
            booking.stripe_payment_intent_id = payment_intent['id']
            booking.amount_paid = Decimal(payment_intent['amount']) / 100
            booking.save()
        except Booking.DoesNotExist:
            pass

    return HttpResponse(status=200)