import json
from datetime import time

from django.forms import inlineformset_factory
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from JobJab.services.models import ServiceListing
from JobJab.booking.models import WeeklyTimeSlot, ProviderAvailability

User = get_user_model()


class BookingUrlsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='user1', password='pass', email='seeker@gmail.com', )
        self.provider = User.objects.create_user(username='provider1', password='pass', email='provider@gmail.com', )

        self.service = ServiceListing.objects.create(
            provider=self.provider,
            title='Sample Service',
            price=100.00,
        )

        self.availability = ProviderAvailability.objects.create(provider=self.provider)

        self.slot = WeeklyTimeSlot.objects.create(
            availability=self.availability,
            day_of_week=1,
            start_time=time(10, 0),
            end_time=time(11, 0),
            is_booked=False,
        )

    def test_create_booking_url_post(self):
        self.client.force_login(self.user)
        url = reverse('booking:create_booking')
        data = {
            'time_slot': self.slot.id,
            'service': self.service.id,
            'notes': 'Please book me!',
        }
        response = self.client.post(url, data=json.dumps(data),
                                    content_type='application/json',
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content,
                             {'success': True, 'booking_id': response.json().get('booking_id'), 'amount': 100.0})

    def test_get_time_slots_url_get(self):
        url = reverse('booking:time_slots', kwargs={'service_id': self.service.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('slots', response.json())

    def test_create_availability_view_get(self):
        self.client.force_login(self.provider)
        url = reverse('booking:set_availability')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'services-display.html')