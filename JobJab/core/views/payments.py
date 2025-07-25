import stripe
from django.shortcuts import render, get_object_or_404
from django.views import View

from JobJab.core.models import CustomUser
from JobJab.subscriptions.models import SubscriptionRecord


class UserPaymentsView(View):
    def get(self, request, username):
        user = get_object_or_404(CustomUser, username=username)
        payments_made = SubscriptionRecord.objects.filter(user=user).order_by('-created_at')

        payment_details = []
        for record in payments_made:
            data = {
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
                    data['status'] = invoice.status
                    data['amount_paid'] = f"${invoice.amount_paid / 100:.2f}" if invoice.amount_paid else None
                    data['date_paid'] = invoice.created
                    data['receipt_url'] = getattr(invoice, 'hosted_invoice_url', None)
                    data['pdf_url'] = getattr(invoice, 'invoice_pdf', None)
                except Exception as e:
                    print(f"Error retrieving invoice {record.stripe_invoice_id}: {e}")
            payment_details.append(data)

        return render(request, 'core/accounts/account-tabs/account_payments.html', {
            'user': user,
            'payment_details': payment_details
        })