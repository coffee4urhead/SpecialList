from datetime import datetime

import stripe
from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from JobJab.core.models import CustomUser
from JobJab.subscriptions.models import Subscription

stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def create_checkout_session(request):
    if request.method == 'POST':
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': 'price_1RgkviRohIG2l47dLU47xuS0',
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url=request.build_absolute_uri(reverse('success')) + '?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=request.build_absolute_uri(reverse('canceled')),
                customer_email=request.user.email,
            )
            return redirect(checkout_session.url, code=303)
        except Exception as e:
            return HttpResponse(str(e))
    return render(request, 'subscriptions/checkout.html')

def success_view(request):
    session_id = request.GET.get('session_id')
    if session_id:
        session = stripe.checkout.Session.retrieve(session_id)
        customer = stripe.Customer.retrieve(session.customer)
        return render(request, 'subscriptions/success.html', {'customer': customer})
    return render(request, 'subscriptions/success.html')

def canceled_view(request):
    return render(request, 'subscriptions/canceled.html')

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
        return HttpResponse(status=400)  # Invalid payload
    except stripe.error.SignatureVerificationError as e:
        return HttpResponse(status=400)  # Invalid signature

    # Handle events
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session(session)  # Your logic here
    elif event['type'] == 'invoice.paid':
        invoice = event['data']['object']
        # handle_invoice_paid(invoice)
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        # handle_payment_failed(invoice)
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        # handle_subscription_deleted(subscription)

    return HttpResponse(status=200)

# Example: Handle successful checkout
def handle_checkout_session(session):
    customer_email = session["customer_details"]["email"]
    subscription_id = session["subscription"]
    customer_id = session["customer"]

    try:
        user = CustomUser.objects.get(email=customer_email)
        subscription = stripe.Subscription.retrieve(subscription_id)

        Subscription.objects.update_or_create(
            user=user,
            defaults={
                'stripe_customer_id': customer_id,
                'stripe_subscription_id': subscription_id,
                'plan': subscription.plan.id,  # or map to your plan types
                'status': subscription.status,
                'cancel_at_period_end': subscription.cancel_at_period_end,
                'current_period_start': datetime.fromtimestamp(subscription.current_period_start),
                'current_period_end': datetime.fromtimestamp(subscription.current_period_end),
            }
        )
    except CustomUser.DoesNotExist:
        print(f"User with email {customer_email} not found")