from datetime import datetime

import stripe
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views import View

from JobJab.booking.models import Booking
from JobJab.core.models import CustomUser, Notification
from JobJab.subscriptions.models import SubscriptionRecord


class UserPaymentsView(View):
    def get(self, request, username):
        user = get_object_or_404(CustomUser, username=username)

        subscription_payments = SubscriptionRecord.objects.filter(user=user).order_by('-created_at')
        booking_payments = Booking.objects.filter(seeker=user, payment_status='paid').order_by('-created_at')

        payment_details = []

        for record in subscription_payments:
            data = {
                'type': 'subscription',
                'record': record,
                'receipt_url': None,
                'pdf_url': None,
                'amount_paid': None,
                'date_paid': None,
                'status': None,
            }
            if record.stripe_invoice_id:
                try:
                    invoice = stripe.Invoice.retrieve(record.stripe_invoice_id)
                    date_paid = timezone.make_aware(datetime.fromtimestamp(invoice.created)) if invoice.created else None

                    data.update({
                        'status': invoice.status,
                        'amount_paid': f"${invoice.amount_paid / 100:.2f}" if invoice.amount_paid else None,
                        'date_paid': date_paid,
                        'receipt_url': invoice.hosted_invoice_url,
                        'pdf_url': invoice.invoice_pdf,
                    })
                except Exception as e:
                    print(f"Error retrieving subscription invoice {record.stripe_invoice_id}: {e}")
            payment_details.append(data)

        for record in booking_payments:
            date_paid = record.created_at
            if record.stripe_invoice_id:
                try:
                    invoice = stripe.Invoice.retrieve(record.stripe_invoice_id)
                    if invoice.status == 'paid':
                        date_paid = timezone.make_aware(datetime.fromtimestamp(invoice.created)) if invoice.created else record.created_at

                        amount_paid = f"${invoice.amount_paid / 100:.2f}" if invoice.amount_paid else f"${record.amount_paid:.2f}"
                        data = {
                            'type': 'booking',
                            'record': record,
                            'receipt_url': invoice.hosted_invoice_url,
                            'pdf_url': invoice.invoice_pdf,
                            'amount_paid': amount_paid,
                            'date_paid': date_paid,
                            'status': 'paid',
                        }
                    else:
                        print(f"Invoice {record.stripe_invoice_id} status: {invoice.status}")
                        data = {
                            'type': 'booking',
                            'record': record,
                            'receipt_url': None,
                            'pdf_url': None,
                            'amount_paid': f"${record.amount_paid:.2f}",
                            'date_paid': record.created_at,
                            'status': record.payment_status,
                        }
                except Exception as e:
                    print(f"Error retrieving booking invoice {record.stripe_invoice_id}: {e}")
                    data = {
                        'type': 'booking',
                        'record': record,
                        'receipt_url': None,
                        'pdf_url': None,
                        'amount_paid': f"${record.amount_paid:.2f}",
                        'date_paid': record.created_at,
                        'status': record.payment_status,
                    }
            else:
                data = {
                    'type': 'booking',
                    'record': record,
                    'receipt_url': None,
                    'pdf_url': None,
                    'amount_paid': f"${record.amount_paid:.2f}",
                    'date_paid': record.created_at,
                    'status': record.payment_status,
                }
            payment_details.append(data)

        # Safe sorting with timezone-aware fallback
        def safe_date_paid(x):
            dt = x.get('date_paid')
            if dt is None:
                return timezone.make_aware(datetime.min)
            if timezone.is_naive(dt):
                return timezone.make_aware(dt)
            return dt

        payment_details.sort(key=safe_date_paid, reverse=True)

        unread_count = 0
        if request.user.is_authenticated:
            unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

        return render(request, 'core/accounts/account-tabs/account_payments.html', {
            'user': user,
            'payment_details': payment_details,
            'unread_count': unread_count,
        })
