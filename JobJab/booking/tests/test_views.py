from datetime import time, date
from decimal import Decimal
import json
from unittest.mock import patch, MagicMock

from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model

from JobJab.booking.models import Booking, WeeklyTimeSlot, ProviderAvailability
from JobJab.services.models import ServiceListing, Availability
from JobJab.booking.views import (
    provider_schedule_api,
    ServiceBookingView,
    get_time_slots,
    create_booking,
    create_payment_intent,
    stripe_webhook,
    booking_confirmation,
    verify_payment,
    download_invoice
)

User = get_user_model()


class ViewsTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='pass')
        self.provider = User.objects.create_user(username='provider', email='provider@example.com', password='pass')

        # Create ProviderAvailability (not Availability)
        self.provider_availability = ProviderAvailability.objects.create(
            provider=self.provider,
            slot_duration=30,
            buffer_time=15,
            is_active=True
        )

        self.service = ServiceListing.objects.create(
            provider=self.provider,
            title='Test Service',
            price=100.00,
        )

        # Create WeeklyTimeSlot linked to ProviderAvailability
        self.slot = WeeklyTimeSlot.objects.create(
            availability=self.provider_availability,
            day_of_week=0,
            start_time=time(9, 12, 2),
            end_time=time(10, 22, 12),
            is_booked=False,
        )

        self.booking = Booking.objects.create(
            seeker=self.user,
            provider=self.provider,
            service=self.service,
            time_slot=self.slot,
            price=self.service.price,
            payment_status='pending'
        )

    def test_provider_schedule_api(self):
        request = self.factory.get('/api/schedule/')
        response = provider_schedule_api(request, provider_id=self.provider.id)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('slots', data)

    def test_get_time_slots(self):
        request = self.factory.get('/get-time-slots/')
        response = get_time_slots(request, service_id=self.service.id)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content.decode('utf-8'))
        self.assertIn('slots', data)

    def test_create_booking_post(self):
        data = {
            'time_slot': self.slot.id,
            'service': self.service.id,
            'notes': 'Test note'
        }
        json_data = json.dumps(data)
        request = self.factory.post(
            '/create-booking/',
            data=json_data,
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'  # This line is key
        )
        request.user = self.user

        response = create_booking(request)
        self.assertEqual(response.status_code, 200)

    @patch('stripe.Customer.create')
    @patch('stripe.Customer.retrieve')
    @patch('stripe.InvoiceItem.create')
    @patch('stripe.PaymentIntent.create')
    @patch('stripe.Invoice.create')
    @patch('stripe.Invoice.finalize_invoice')
    def test_create_payment_intent(self, mock_finalize, mock_invoice_create, mock_payment_intent_create,
                                   mock_invoice_item_create, mock_customer_retrieve, mock_customer_create):
        request = self.factory.get('/')
        request.user = self.user

        mock_customer = MagicMock()
        mock_customer.id = 'cus_test'
        mock_customer_create.return_value = mock_customer
        mock_customer_retrieve.return_value = mock_customer

        mock_payment_intent = MagicMock()
        mock_payment_intent.id = 'pi_test'
        mock_payment_intent.client_secret = 'secret_test'
        mock_payment_intent_create.return_value = mock_payment_intent

        mock_invoice = MagicMock()
        mock_invoice.id = 'inv_test'
        mock_invoice_create.return_value = mock_invoice
        mock_finalize.return_value = mock_invoice

        response = create_payment_intent(request, booking_id=self.booking.id)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('clientSecret', data)

    @patch('stripe.Webhook.construct_event')
    def test_stripe_webhook_payment_intent_succeeded(self, mock_construct_event):
        request = self.factory.post('/stripe-webhook/', data=b'{}', content_type='application/json')
        request.META['HTTP_STRIPE_SIGNATURE'] = 'testsignature'

        event = {
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'metadata': {'booking_id': self.booking.id},
                    'id': 'pi_123',
                    'amount': 10000,
                }
            }
        }
        mock_construct_event.return_value = event

        response = stripe_webhook(request)
        self.assertEqual(response.status_code, 200)

    def test_booking_confirmation(self):
        url = reverse('booking:booking_confirmed', args=[self.booking.id])
        request = self.factory.get(url)
        request.user = self.user

        response = booking_confirmation(request, booking_id=self.booking.id)
        self.assertEqual(response.status_code, 200)

    @patch('stripe.PaymentIntent.retrieve')
    @patch('stripe.Invoice.retrieve')
    def test_verify_payment(self, mock_invoice_retrieve, mock_payment_intent_retrieve):
        request = self.factory.get('/')
        request.user = self.user

        mock_payment_intent = MagicMock()
        mock_payment_intent.status = 'succeeded'
        mock_payment_intent.amount = 10000
        mock_payment_intent_retrieve.return_value = mock_payment_intent

        mock_invoice = MagicMock()
        mock_invoice.invoice_pdf = 'pdf_url'
        mock_invoice.number = '123'
        mock_invoice.status = 'paid'
        mock_invoice.amount_paid = 10000
        mock_invoice.created = 123456
        mock_invoice_retrieve.return_value = mock_invoice

        self.booking.stripe_payment_intent_id = 'pi_test'
        self.booking.stripe_invoice_id = 'inv_test'
        self.booking.save()

        response = verify_payment(request, booking_id=self.booking.id)
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'paid')
        self.assertIn('invoice', data)

    def test_download_invoice_unauthorized(self):
        request = self.factory.get('/')
        request.user = User.objects.create_user(username='otheruser', password='pass')
        self.booking.stripe_invoice_id = 'inv_test'
        self.booking.save()

        response = download_invoice(request, booking_id=self.booking.id)
        self.assertEqual(response.status_code, 403)

    @patch('stripe.Invoice.retrieve')
    def test_download_invoice_success(self, mock_invoice_retrieve):
        request = self.factory.get('/')
        request.user = self.user
        self.booking.stripe_invoice_id = 'inv_test'
        self.booking.save()

        mock_invoice = MagicMock()
        mock_invoice.invoice_pdf = 'http://stripe.com/invoice.pdf'
        mock_invoice_retrieve.return_value = mock_invoice

        response = download_invoice(request, booking_id=self.booking.id)
        self.assertEqual(response.status_code, 302)  # Redirect to PDF URL
