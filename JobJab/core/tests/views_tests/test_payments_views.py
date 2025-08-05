from django.template.response import TemplateResponse
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from django.http import Http404

from JobJab.core.models import CustomUser, Notification
from JobJab.core.views.payments import UserPaymentsView
from JobJab.subscriptions.models import SubscriptionRecord
from JobJab.booking.models import Booking
from JobJab.services.models import ServiceListing


class UserPaymentsViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            user_type='seeker'
        )
        self.other_user = CustomUser.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123',
            user_type='seeker'
        )
        self.provider = CustomUser.objects.create_user(
            username='provider',
            email='provider@example.com',
            password='testpass123',
            user_type='provider'
        )

        self.service = ServiceListing.objects.create(
            provider=self.provider,
            title='Test Service',
            price=100.00
        )

        self.subscription1 = SubscriptionRecord.objects.create(
            user=self.user,
            stripe_customer_id='cus_test1',
            stripe_subscription_id='sub_test1',
            stripe_price_id='price_test1',
            stripe_invoice_id='inv_test1',
            plan='Starter',
            status='active',
            price=9.99,
            created_at=timezone.now() - timedelta(days=2)
        )
        self.subscription2 = SubscriptionRecord.objects.create(
            user=self.user,
            stripe_customer_id='cus_test2',
            stripe_subscription_id='sub_test2',
            stripe_price_id='price_test2',
            stripe_invoice_id='inv_test2',
            plan='Growth',
            status='active',
            price=19.99,
            created_at=timezone.now() - timedelta(days=1)
        )

        self.booking1 = Booking.objects.create(
            seeker=self.user,
            provider=self.provider,
            service=self.service,
            appointment_datetime=timezone.now() + timedelta(days=1),
            status='confirmed',
            payment_status='paid',
            amount_paid=100.00,
            price=100.00,
            stripe_invoice_id='inv_booking1',
            created_at=timezone.now() - timedelta(days=3)
        )
        self.booking2 = Booking.objects.create(
            seeker=self.user,
            provider=self.provider,
            service=self.service,
            appointment_datetime=timezone.now() + timedelta(days=2),
            status='confirmed',
            payment_status='paid',
            amount_paid=150.00,
            price=150.00,
            stripe_invoice_id=None,
            created_at=timezone.now() - timedelta(days=4)
        )

        Notification.objects.create(
            user=self.user,
            title="Test Notification",
            message="This is a test",
            is_read=False
        )

    def test_get_authenticated_user_viewing_own_payments(self):
        self.client.login(username='testuser', password='testpass123')

        with patch('stripe.Invoice.retrieve') as mock_retrieve:
            mock_invoice = MagicMock()
            mock_invoice.status = 'paid'
            mock_invoice.amount_paid = 10000
            mock_invoice.created = int(datetime.now().timestamp())
            mock_invoice.hosted_invoice_url = 'http://example.com/receipt'
            mock_invoice.invoice_pdf = 'http://example.com/pdf'
            mock_retrieve.return_value = mock_invoice

            response = self.client.get(reverse('user_payments', kwargs={'username': 'testuser'}))

        self.assertEqual(response.status_code, 200)
        context = response.context

        self.assertEqual(context['user'], self.user)
        self.assertEqual(context['unread_count'], 1)

        payment_details = context['payment_details']
        self.assertEqual(len(payment_details), 4)

        records = [p['record'] for p in payment_details]
        self.assertIn(self.subscription1, records)
        self.assertIn(self.subscription2, records)
        self.assertIn(self.booking1, records)
        self.assertIn(self.booking2, records)

    def test_get_authenticated_user_viewing_other_user_payments(self):
        self.client.login(username='testuser', password='testpass123')

        response = self.client.get(reverse('user_payments', kwargs={'username': 'otheruser'}))

        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response['Content-Type'])

        context = response.context
        self.assertEqual(context['user'].username, 'otheruser')
        self.assertEqual(len(context['payment_details']), 0)

    def test_get_user_not_found(self):
        request = self.factory.get(reverse('user_payments', kwargs={'username': 'nonexistent'}))
        request.user = self.user

        with self.assertRaises(Http404):
            UserPaymentsView.as_view()(request, username='nonexistent')