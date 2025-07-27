import stripe
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views import View

from JobJab.booking.models import Booking
from JobJab.core.models import CustomUser
from JobJab.subscriptions.models import SubscriptionRecord


class UserPaymentsView(View):
    def get(self, request, username):
        user = get_object_or_404(CustomUser, username=username)

        # Get all payment records
        subscription_payments = SubscriptionRecord.objects.filter(user=user).order_by('-created_at')
        booking_payments = Booking.objects.filter(seeker=user, payment_status='paid').order_by('-created_at')

        payment_details = []

        # Process subscription payments
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
                    data.update({
                        'status': invoice.status,
                        'amount_paid': f"${invoice.amount_paid / 100:.2f}" if invoice.amount_paid else None,
                        'date_paid': timezone.make_aware(
                            timezone.datetime.fromtimestamp(invoice.created)) if invoice.created else None,
                        'receipt_url': invoice.hosted_invoice_url,
                        'pdf_url': invoice.invoice_pdf,
                    })
                except Exception as e:
                    print(f"Error retrieving subscription invoice {record.stripe_invoice_id}: {e}")
            payment_details.append(data)

        # Process booking payments
        for record in booking_payments:
            data = {
                'type': 'booking',
                'record': record,
                'receipt_url': None,
                'pdf_url': None,
                'amount_paid': f"${record.amount_paid:.2f}" if record.amount_paid else None,
                'date_paid': record.created_at,
                'status': record.payment_status,
            }
            print(record.stripe_invoice_id)
            if record.stripe_invoice_id:
                try:
                    invoice = stripe.Invoice.retrieve(record.stripe_invoice_id)
                    print(invoice.status)
                    if invoice.status == 'paid':  # Only show URLs for paid invoices
                        data.update({
                            'receipt_url': invoice.hosted_invoice_url,
                            'pdf_url': invoice.invoice_pdf,
                            'status': 'paid',
                            'amount_paid': f"${invoice.amount_paid / 100:.2f}" if invoice.amount_paid else f"${record.amount_paid:.2f}",
                            'date_paid': timezone.make_aware(timezone.datetime.fromtimestamp(
                                invoice.created)) if invoice.created else record.created_at,
                        })
                    else:
                        print(f"Invoice {record.stripe_invoice_id} status: {invoice.status}")
                except Exception as e:
                    print(f"Error retrieving booking invoice {record.stripe_invoice_id}: {e}")
            payment_details.append(data)

        # Sort all payments by date (newest first)
        payment_details.sort(key=lambda x: x['date_paid'] if x['date_paid'] else 0, reverse=True)

        return render(request, 'core/accounts/account-tabs/account_payments.html', {
            'user': user,
            'payment_details': payment_details
        })
