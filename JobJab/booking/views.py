import json
from decimal import Decimal
from collections import defaultdict

import stripe
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import modelformset_factory
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
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
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form = BookingForm(request.POST)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.seeker = request.user
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)

            slot_id = data.get('time_slot')
            service_id = data.get('service')
            notes = data.get('notes')

            if slot_id:
                booking.time_slot = get_object_or_404(WeeklyTimeSlot, id=slot_id)
            else:
                return JsonResponse({'error': 'Missing time_slot'}, status=400)
            if not service_id:
                return JsonResponse({'error': 'Missing service'}, status=400)

            booking.time_slot = get_object_or_404(WeeklyTimeSlot, id=slot_id)
            booking.service = get_object_or_404(ServiceListing, id=service_id)
            booking.provider = booking.service.provider
            booking.notes = notes

            booking.price = booking.service.price

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


def create_payment_intent(request, booking_id):
    try:
        booking = Booking.objects.get(id=booking_id)
        amount = int(booking.price * 100)

        # Create or retrieve customer
        if not booking.stripe_customer_id:
            customer = stripe.Customer.create(
                email=request.user.email,
                name=f"{request.user.first_name} {request.user.last_name}",
                metadata={
                    'user_id': request.user.id,
                    'booking_id': booking_id
                }
            )
            booking.stripe_customer_id = customer.id
            booking.save()
        else:
            customer = stripe.Customer.retrieve(booking.stripe_customer_id)

        # Create invoice item
        stripe.InvoiceItem.create(
            customer=customer.id,
            amount=amount,
            currency='usd',
            description=f"Service: {booking.service.title}",
            metadata={
                'booking_id': booking.id,
                'service_id': booking.service.id
            }
        )

        # Create payment intent
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',
            customer=customer.id,
            automatic_payment_methods={'enabled': True},
            metadata={
                'booking_id': booking.id,
                'service_id': booking.service.id,
                'user_id': request.user.id
            }
        )

        # Create invoice (optional, if you still want to create it)
        invoice = stripe.Invoice.create(
            customer=customer.id,
            collection_method='charge_automatically',
            auto_advance=True,
            metadata={'booking_id': booking.id}
        )
        finalized_invoice = stripe.Invoice.finalize_invoice(invoice.id)

        # Update booking with all IDs
        booking.stripe_customer_id = customer.id
        booking.stripe_payment_intent_id = intent.id
        booking.stripe_invoice_id = finalized_invoice.id
        booking.save()

        return JsonResponse({
            'clientSecret': intent.client_secret,
            'booking_id': booking.id,
            'invoice_id': finalized_invoice.id
        })

    except Exception as e:
        print(f"Error in create_payment_intent: {str(e)}")
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    event = None

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        print(f"Webhook signature error: {str(e)}")
        return HttpResponse(status=400)

    # Handle successful payment intent
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        booking_id = payment_intent['metadata'].get('booking_id')

        if not booking_id:
            print("Missing booking_id in payment_intent metadata")
            return HttpResponse(status=400)

        try:
            booking = Booking.objects.get(id=booking_id)
            booking.payment_status = 'paid'
            booking.stripe_payment_intent_id = payment_intent['id']

            # Only set amount_paid if no invoice exists
            if not booking.stripe_invoice_id:
                booking.amount_paid = Decimal(payment_intent['amount']) / 100

            booking.save()
        except Booking.DoesNotExist:
            print(f"Booking {booking_id} not found")
            return HttpResponse(status=404)

    # Handle invoice paid
    elif event['type'] == 'invoice.paid':
        invoice = event['data']['object']
        booking_id = invoice['metadata'].get('booking_id')

        if booking_id:
            try:
                booking = Booking.objects.get(id=booking_id)
                booking.payment_status = 'paid'
                booking.stripe_invoice_id = invoice.id
                booking.amount_paid = Decimal(invoice['amount_paid']) / 100
                booking.save()
                print(f"Invoice paid. Booking {booking_id} updated with amount: {booking.amount_paid}")
            except Booking.DoesNotExist:
                print(f"Booking {booking_id} not found for invoice")
                return HttpResponse(status=404)

    return HttpResponse(status=200)


def booking_confirmation(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    payment_intent_id = request.GET.get('payment_intent')

    if payment_intent_id:
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            if payment_intent.status == 'succeeded':
                booking.payment_status = 'paid'
                booking.amount_paid = Decimal(payment_intent.amount) / 100

                # If we have an invoice ID, retrieve the invoice PDF
                invoice_pdf_url = None
                if booking.stripe_invoice_id:
                    try:
                        invoice = stripe.Invoice.retrieve(booking.stripe_invoice_id)
                        if invoice.status == 'paid':
                            invoice_pdf_url = invoice.invoice_pdf
                    except stripe.error.StripeError as e:
                        print(f"Error retrieving invoice: {str(e)}")

                booking.save()

                context = {
                    'booking': booking,
                    'status': 'succeeded',
                    'invoice_pdf_url': invoice_pdf_url,
                    'payment_intent': payment_intent_id,
                }
                return render(request, 'confirmation.html', context)
        except Exception as e:
            print(f"Error verifying payment: {str(e)}")

    context = {
        'booking': booking,
        'status': request.GET.get('redirect_status', ''),
        'payment_intent': request.GET.get('payment_intent'),
        'payment_intent_client_secret': request.GET.get('payment_intent_client_secret'),
        'redirect_status': request.GET.get('redirect_status')
    }
    return render(request, 'confirmation.html', context)


def verify_payment(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    if booking.stripe_payment_intent_id:
        try:
            payment_intent = stripe.PaymentIntent.retrieve(booking.stripe_payment_intent_id)
            if payment_intent.status == 'succeeded':
                booking.payment_status = 'paid'
                booking.amount_paid = Decimal(payment_intent.amount) / 100

                # Get invoice details if available
                invoice_details = None
                if booking.stripe_invoice_id:
                    try:
                        invoice = stripe.Invoice.retrieve(booking.stripe_invoice_id)
                        invoice_details = {
                            'pdf_url': invoice.invoice_pdf,
                            'number': invoice.number,
                            'status': invoice.status,
                            'amount_paid': invoice.amount_paid / 100,
                            'created': invoice.created,
                        }
                    except stripe.error.StripeError as e:
                        print(f"Error retrieving invoice: {str(e)}")

                booking.save()
                return JsonResponse({
                    'status': 'paid',
                    'invoice': invoice_details
                })
            return JsonResponse({'status': payment_intent.status})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)

    return JsonResponse({'status': 'no_payment_intent'})


@login_required
def download_invoice(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)

    # Verify the requesting user has permission to access this invoice
    if request.user != booking.seeker and request.user != booking.provider:
        return HttpResponse("Unauthorized", status=403)

    if not booking.stripe_invoice_id:
        return HttpResponse("No invoice available for this booking", status=404)

    try:
        invoice = stripe.Invoice.retrieve(booking.stripe_invoice_id)
        if not invoice.invoice_pdf:
            return HttpResponse("Invoice PDF not available", status=404)

        # Redirect to Stripe's hosted invoice PDF
        return redirect(invoice.invoice_pdf)

    except stripe.error.StripeError as e:
        print(f"Error retrieving invoice: {str(e)}")
        return HttpResponse("Error retrieving invoice", status=500)
