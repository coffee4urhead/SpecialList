import os
from datetime import timedelta

import stripe
from django.conf import settings
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from JobJab.core.models import CustomUser
from JobJab.subscriptions.models import Subscription, SubscriptionPlan, SubscriptionStatus, SubscriptionRecord

stripe.api_key = settings.STRIPE_SECRET_KEY

PRICE_IDS = {
    SubscriptionPlan.STARTER: os.getenv('STARTER_PLAN_PRICE_ID'),
    SubscriptionPlan.GROWTH: os.getenv('GROWTH_PLAN_PRICE_ID'),
    SubscriptionPlan.ELITE: os.getenv('ELITE_PLAN_PRICE_ID'),
}

PRICE_ID_TO_PLAN = {v: k for k, v in PRICE_IDS.items()}


@require_POST
@login_required(login_url='login')
def create_checkout_session(request, plan_type):
    try:
        normalized_plan = plan_type.upper()
        plan = getattr(SubscriptionPlan, normalized_plan, None)
        price_id = PRICE_IDS.get(plan)

        if not price_id:
            return HttpResponse("Invalid plan type", status=400)

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.build_absolute_uri(reverse('success')) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.build_absolute_uri(reverse('canceled')),
            customer_email=request.user.email,
            metadata={'plan': plan.value},
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return HttpResponse(str(e), status=500)


@login_required(login_url='login')
def success_view(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        return render(request, 'subscriptions/success.html')

    try:
        # Retrieve the session with expanded subscription
        session = stripe.checkout.Session.retrieve(
            session_id,
            expand=['subscription', 'subscription.latest_invoice']
        )

        if not session.subscription:
            return render(request, 'subscriptions/success.html')

        # Get the subscription ID as string
        subscription_id = session.subscription.id

        # Get the invoice ID if it exists
        invoice_id = None
        if hasattr(session.subscription, 'latest_invoice') and session.subscription.latest_invoice:
            invoice_id = session.subscription.latest_invoice.id

        # Get price details
        price_id = session.subscription['items']['data'][0]['price']['id']
        amount = session.subscription['items']['data'][0]['price']['unit_amount'] / 100
        plan = session.metadata.get('plan', SubscriptionPlan.STARTER)

        current_start = timezone.now()
        current_end = current_start + timedelta(days=31)

        user = request.user
        subscription, _ = Subscription.objects.update_or_create(
            user=user,
            defaults={
                'stripe_customer_id': session.customer,
                'stripe_subscription_id': subscription_id,  # Use the string ID
                'stripe_price_id': price_id,
                'stripe_invoice_id': invoice_id,
                'plan': plan,
                'status': session.subscription.status,
                'price': amount,
                'cancel_at_period_end': session.subscription.cancel_at_period_end,
                'current_period_start': current_start,
                'current_period_end': current_end,
            }
        )

        SubscriptionRecord.objects.create(
            user=user,
            plan=plan,
            stripe_customer_id=session.customer,
            stripe_subscription_id=subscription_id,
            stripe_price_id=price_id,
            stripe_invoice_id=invoice_id,
            status=session.subscription.status,
            price=amount,
            cancel_at_period_end=session.subscription.cancel_at_period_end,
            current_period_start=current_start,
            current_period_end=current_end
        )

        user.subscription_membership = subscription
        user.save()

        return render(request, 'subscriptions/success.html')
    except Exception as e:
        print(f"Failed to attach subscription in success_view: {e}")
        return render(request, 'subscriptions/success.html')


@login_required(login_url='login')
def canceled_view(request):
    return render(request, 'subscriptions/canceled.html')


@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    event_type = event['type']
    obj = event['data']['object']

    if event_type == 'invoice.payment_succeeded':
        handle_invoice_payment_succeeded(obj)
    elif event_type == 'checkout.session.completed':
        handle_checkout_session(obj)
    elif event_type == 'customer.subscription.deleted':
        handle_subscription_deleted(obj)
    elif event_type == 'customer.subscription.updated':
        handle_subscription_updated(obj)
    elif event_type == 'invoice.payment_failed':
        handle_payment_failed(obj)
    elif event_type == 'invoice.finalized':
        handle_invoice_finalized(obj)

    return HttpResponse(status=200)


def detect_plan_from_price_id(price_id):
    return PRICE_ID_TO_PLAN.get(price_id, SubscriptionPlan.STARTER)


def handle_invoice_payment_succeeded(invoice):
    stripe_customer_id = invoice.get("customer")
    stripe_subscription_id = invoice.get("subscription")
    invoice_id = invoice.get("id")  # Use the invoice's own ID

    amount = invoice.get('amount_paid', 0) / 100

    price_id = None
    try:
        line_item = invoice['lines']['data'][0]
        price_id = line_item.get('price', {}).get('id')
    except Exception:
        pass

    user = CustomUser.objects.filter(subscription__stripe_customer_id=stripe_customer_id).first()

    if not user:
        customer_email = invoice.get("customer_email") or invoice.get("receipt_email")
        if customer_email:
            user = CustomUser.objects.filter(email=customer_email).first()

    if not user:
        return

    plan = detect_plan_from_price_id(price_id)
    current_start = timezone.now()
    current_end = current_start + timedelta(days=31)

    try:
        stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        cancel_at_period_end = stripe_subscription.cancel_at_period_end
    except Exception:
        cancel_at_period_end = False

    sub, _ = Subscription.objects.update_or_create(
        user=user,
        defaults={
            'stripe_customer_id': stripe_customer_id,
            'stripe_subscription_id': stripe_subscription_id,
            'stripe_price_id': price_id,
            'price': amount,
            'stripe_invoice_id': invoice_id,
            'status': SubscriptionStatus.ACTIVE,
            'plan': plan,
            'cancel_at_period_end': cancel_at_period_end,
            'current_period_start': current_start,
            'current_period_end': current_end
        }
    )

    SubscriptionRecord.objects.create(
        user=user,
        plan=plan,
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=stripe_subscription_id,
        stripe_invoice_id=invoice_id,
        stripe_price_id=price_id,
        status=SubscriptionStatus.ACTIVE,
        price=amount,
        cancel_at_period_end=cancel_at_period_end,
        current_period_start=current_start,
        current_period_end=current_end
    )
    user.subscription_membership = sub
    user.save()


def handle_checkout_session(session):
    try:
        customer_email = session.get("customer_details", {}).get("email")
        if not customer_email:
            return

        subscription_id = session.get("subscription")
        if not subscription_id:
            return

        stripe_subscription = stripe.Subscription.retrieve(subscription_id)
        latest_invoice = stripe_subscription.latest_invoice

        # Get the invoice object if it exists
        invoice_id = None
        if latest_invoice:
            invoice = stripe.Invoice.retrieve(latest_invoice)
            invoice_id = invoice.id

        customer_id = session.get("customer")
        plan = session.get("metadata", {}).get("plan", SubscriptionPlan.STARTER)

        user = CustomUser.objects.get(email=customer_email)

        price_id = stripe_subscription['items']['data'][0]['price']['id']
        amount = stripe_subscription['items']['data'][0]['price']['unit_amount'] / 100

        current_start = timezone.now()
        current_end = current_start + timedelta(days=30)

        subscription, _ = Subscription.objects.update_or_create(
            user=user,
            defaults={
                'stripe_customer_id': customer_id,
                'stripe_subscription_id': subscription_id,
                'stripe_invoice_id': invoice_id,
                'stripe_price_id': price_id,
                'plan': plan,
                'status': stripe_subscription.status,
                'price': amount,
                'cancel_at_period_end': stripe_subscription.cancel_at_period_end,
                'current_period_start': current_start,
                'current_period_end': current_end,
            }
        )

        SubscriptionRecord.objects.create(
            user=user,
            plan=plan,
            stripe_customer_id=customer_id,
            stripe_subscription_id=subscription_id,
            stripe_invoice_id=invoice_id,
            stripe_price_id=price_id,
            status=stripe_subscription.status,
            price=amount,
            cancel_at_period_end=stripe_subscription.cancel_at_period_end,
            current_period_start=current_start,
            current_period_end=current_end
        )

        user.subscription_membership = subscription
        user.save()

    except CustomUser.DoesNotExist:
        print(f"User with email {customer_email} not found")
    except Exception as e:
        print(f"Error handling checkout session: {str(e)}")


def handle_invoice_finalized(invoice):
    stripe_customer_id = invoice.get("customer")
    stripe_subscription_id = invoice.get("subscription")
    invoice_id = invoice.get("id")  # This is the correct invoice ID

    # Get email from invoice (customer_email is provided)
    customer_email = invoice.get("customer_email")

    user = CustomUser.objects.filter(subscription__stripe_customer_id=stripe_customer_id).first()
    if not user and customer_email:
        user = CustomUser.objects.filter(email=customer_email).first()

    if not user:
        print(f"Invoice Finalized: User not found for customer ID {stripe_customer_id}")
        return

    # Get plan from line item
    try:
        line_item = invoice['lines']['data'][0]
        price_id = line_item.get('price', {}).get('id')
    except (IndexError, KeyError, TypeError):
        price_id = None

    plan = detect_plan_from_price_id(price_id)
    amount = invoice.get('amount_due', 0) / 100

    current_start = timezone.now()
    current_end = current_start + timedelta(days=30)

    try:
        stripe_subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        cancel_at_period_end = stripe_subscription.cancel_at_period_end
        status = stripe_subscription.status
    except Exception:
        cancel_at_period_end = False
        status = SubscriptionStatus.ACTIVE

    subscription, _ = Subscription.objects.update_or_create(
        user=user,
        defaults={
            'stripe_customer_id': stripe_customer_id,
            'stripe_subscription_id': stripe_subscription_id,
            'stripe_price_id': price_id,
            'stripe_invoice_id': invoice_id,
            'plan': plan,
            'status': status,
            'price': amount,
            'cancel_at_period_end': cancel_at_period_end,
            'current_period_start': current_start,
            'current_period_end': current_end
        }
    )

    SubscriptionRecord.objects.create(
        user=user,
        plan=plan,
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=stripe_subscription_id,
        stripe_price_id=price_id,
        stripe_invoice_id=invoice_id,
        status=status,
        price=amount,
        cancel_at_period_end=cancel_at_period_end,
        current_period_start=current_start,
        current_period_end=current_end
    )

    user.subscription_membership = subscription
    user.save()


def handle_subscription_deleted(subscription):
    try:
        sub = Subscription.objects.get(stripe_subscription_id=subscription['id'])
        sub.status = SubscriptionStatus.CANCELED
        sub.save()
    except Subscription.DoesNotExist:
        pass


def handle_subscription_updated(subscription):
    try:
        sub = Subscription.objects.get(stripe_subscription_id=subscription['id'])
        sub.status = subscription['status']
        sub.cancel_at_period_end = subscription.get('cancel_at_period_end', False)
        sub.current_period_start = subscription['current_period_start']
        sub.current_period_end = subscription['current_period_end']
        sub.save()
    except Subscription.DoesNotExist:
        pass


def handle_payment_failed(invoice):
    try:
        sub = Subscription.objects.get(stripe_subscription_id=invoice.get('subscription'))
        sub.status = SubscriptionStatus.PAST_DUE
        sub.save()
    except Subscription.DoesNotExist:
        pass


def offer_plans(request):
    return render(request, 'subscriptions/offer-plans-page.html')
