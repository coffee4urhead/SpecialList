import stripe
from django.shortcuts import render, get_object_or_404

from JobJab.core.models import CustomUser
from JobJab.subscriptions.models import SubscriptionRecord


def user_payments(request, username):
    user = get_object_or_404(CustomUser, username=username)
    payments_made = SubscriptionRecord.objects.filter(user=user).order_by('-created_at')

    payment_details = []
    for record in payments_made:
        payment_data = {
            'record': record,
            'receipt_url': None,
            'pdf_url': None,
            'amount_paid': None,
            'date_paid': None,
            'status': None
        }

        if record.stripe_invoice_id:
            try:
                # Only retrieve basic invoice info without expanding
                invoice = stripe.Invoice.retrieve(
                    record.stripe_invoice_id,
                    expand=[]  # Don't expand anything to minimize issues
                )

                payment_data['status'] = invoice.status
                payment_data['amount_paid'] = f"${invoice.amount_paid / 100:.2f}" if invoice.amount_paid else None
                payment_data['date_paid'] = invoice.created

                # Use direct URLs from the invoice without processing
                if hasattr(invoice, 'hosted_invoice_url'):
                    payment_data['receipt_url'] = invoice.hosted_invoice_url
                if hasattr(invoice, 'invoice_pdf'):
                    payment_data['pdf_url'] = invoice.invoice_pdf

            except stripe.error.InvalidRequestError as e:
                print(f"Stripe error retrieving invoice {record.stripe_invoice_id}: {e}")
            except Exception as e:
                print(f"Error processing invoice {record.stripe_invoice_id}: {e}")

        payment_details.append(payment_data)

    context = {
        'user': user,
        'payment_details': payment_details,
    }

    return render(request, 'core/accounts/account-tabs/account_payments.html', context)
