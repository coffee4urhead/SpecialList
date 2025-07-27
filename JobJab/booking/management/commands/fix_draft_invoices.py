from django.core.management.base import BaseCommand
import stripe
from JobJab.booking.models import Booking


class Command(BaseCommand):
    help = 'Fix draft invoices by finalizing and paying them'

    def handle(self, *args, **options):
        draft_bookings = Booking.objects.filter(
            payment_status='paid',
            stripe_invoice_id__isnull=False
        )

        for booking in draft_bookings:
            try:
                invoice = stripe.Invoice.retrieve(booking.stripe_invoice_id)

                if invoice.status == 'draft':
                    # Finalize the invoice
                    finalized = stripe.Invoice.finalize_invoice(invoice.id)
                    self.stdout.write(f"Finalized invoice {finalized.id} for booking {booking.id}")

                    # Pay the invoice if needed
                    if finalized.status == 'open':
                        paid = stripe.Invoice.pay(finalized.id)
                        self.stdout.write(f"Paid invoice {paid.id} for booking {booking.id}")
                        booking.stripe_invoice_id = paid.id
                        booking.save()

            except Exception as e:
                self.stderr.write(f"Error processing booking {booking.id}: {str(e)}")