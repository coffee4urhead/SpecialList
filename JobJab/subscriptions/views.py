from datetime import datetime

import stripe
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from JobJab.core.models import CustomUser
from JobJab.subscriptions.models import Subscription, SubscriptionPlan, SubscriptionStatus

stripe.api_key = settings.STRIPE_SECRET_KEY


@require_POST
@login_required(login_url='login')
def create_checkout_session(request, plan_type):
    try:
        normalized_plan = plan_type.capitalize()
        price_ids = {
            SubscriptionPlan.STARTER: 'price_1RgkviRohIG2l47dLU47xuS0',
            SubscriptionPlan.GROWTH: 'price_1RgkwRRohIG2l47dVCnWv3Ih',
            SubscriptionPlan.ELITE: 'price_1Rgkx5RohIG2l47d7CvQS7Ti'
        }
        price_id = price_ids.get(normalized_plan)
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
            customer_email=request.user.email if request.user.is_authenticated else None,
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        return HttpResponse(str(e), status=500)


@login_required(login_url='login')
def success_view(request):
    session_id = request.GET.get('session_id')
    if session_id:
        session = stripe.checkout.Session.retrieve(session_id)
        customer = stripe.Customer.retrieve(session.customer)
        return render(request, 'subscriptions/success.html', {'customer': customer})
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
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)

    if event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        stripe_customer_id = invoice.get("customer")
        stripe_subscription_id = invoice.get("subscription")
        amount = invoice.get('amount_paid', 0) / 100

        price_id = None
        try:
            line_item = invoice['lines']['data'][0]
            price_id = line_item.get('price', {}).get('id')
        except Exception:
            pass

        user = None
        if stripe_customer_id:
            user = CustomUser.objects.filter(subscription__stripe_customer_id=stripe_customer_id).first()

        if not user:
            customer_email = invoice.get("customer_email") or invoice.get("receipt_email")
            if customer_email:
                user = CustomUser.objects.filter(email=customer_email).first()

        if not user:
            return HttpResponse(status=404)

        sub, created = Subscription.objects.update_or_create(
            user=user,
            defaults={
                'stripe_customer_id': stripe_customer_id or '',
                'stripe_subscription_id': stripe_subscription_id or '',
                'stripe_price_id': price_id or '',
                'price': amount,
                'status': SubscriptionStatus.ACTIVE,
                'plan': detect_plan_from_price_id(price_id),
            }
        )

    elif event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_checkout_session(session)

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_deleted(subscription)

    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_updated(subscription)

    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        handle_payment_failed(invoice)

    return HttpResponse(status=200)


def detect_plan_from_price_id(price_id):
    if not price_id:
        return SubscriptionPlan.STARTER

    price_id_lower = price_id.lower()
    if 'elite' in price_id_lower:
        return SubscriptionPlan.ELITE
    elif 'growth' in price_id_lower:
        return SubscriptionPlan.GROWTH
    else:
        return SubscriptionPlan.STARTER


def handle_checkout_session(session):
    customer_email = session["customer_details"]["email"]
    subscription_id = session["subscription"]
    customer_id = session["customer"]

    try:
        user = CustomUser.objects.get(email=customer_email)

        stripe_subscription = stripe.Subscription.retrieve(subscription_id)
        price_id = stripe_subscription['items']['data'][0]['price']['id']

        plan = detect_plan_from_price_id(price_id)

        Subscription.objects.update_or_create(
            user=user,
            defaults={
                'stripe_customer_id': customer_id,
                'stripe_subscription_id': subscription_id,
                'plan': plan,
                'status': stripe_subscription.status,
                'cancel_at_period_end': stripe_subscription.cancel_at_period_end,
                'current_period_start': datetime.fromtimestamp(stripe_subscription.current_period_start),
                'current_period_end': datetime.fromtimestamp(stripe_subscription.current_period_end),
            }
        )
    except CustomUser.DoesNotExist:
        pass
    except Exception:
        pass


def handle_subscription_deleted(subscription):
    subscription_id = subscription['id']

    try:
        subscription_obj = Subscription.objects.get(stripe_subscription_id=subscription_id)
        subscription_obj.status = SubscriptionStatus.CANCELED
        subscription_obj.save()
    except Subscription.DoesNotExist:
        pass


def handle_subscription_updated(subscription):
    subscription_id = subscription['id']

    try:
        db_subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
        db_subscription.status = subscription['status']
        db_subscription.cancel_at_period_end = subscription.get('cancel_at_period_end', False)
        db_subscription.current_period_start = datetime.fromtimestamp(subscription['current_period_start'])
        db_subscription.current_period_end = datetime.fromtimestamp(subscription['current_period_end'])
        db_subscription.save()
    except Subscription.DoesNotExist:
        pass


def handle_payment_failed(invoice):
    subscription_id = invoice.get('subscription')

    try:
        subscription_obj = Subscription.objects.get(stripe_subscription_id=subscription_id)
        subscription_obj.status = SubscriptionStatus.PAST_DUE
        subscription_obj.save()
    except Subscription.DoesNotExist:
        pass
