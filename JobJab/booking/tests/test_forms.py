from django.test import TestCase
from datetime import datetime, time, timedelta
from ..forms import ProviderAvailabilityForm, WeeklyTimeSlotForm, BookingForm
from ..models import ProviderAvailability, WeeklyTimeSlot, Booking, BookingStatus
from JobJab.services.models import ServiceListing
from django.contrib.auth import get_user_model

User = get_user_model()


class FormsTestCase(TestCase):
    def setUp(self):
        self.provider = User.objects.create_user(username='provider', password='pass', email='provider@gmail.com')
        self.seeker = User.objects.create_user(username='seeker', password='pass', email='seeker@gmail.com')
        self.service = ServiceListing.objects.create(
            provider=self.provider,
            title="Test Service",
            price=50.00
        )

    def test_provider_availability_form_valid(self):
        form_data = {
            'slot_duration': 30,
            'buffer_time': 10,
        }
        form = ProviderAvailabilityForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_provider_availability_invalid_slot_duration(self):
        form_data = {
            'slot_duration': 17,
            'buffer_time': 10,
        }
        form = ProviderAvailabilityForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('slot_duration', form.errors)

    def test_weekly_time_slot_form_valid(self):
        form_data = {
            'day_of_week': 2,
            'start_time': time(10, 0),
            'end_time': time(11, 0),
            'is_booked': False
        }
        form = WeeklyTimeSlotForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_weekly_time_slot_invalid_times(self):
        form_data = {
            'day_of_week': 2,
            'start_time': time(15, 0),
            'end_time': time(14, 0),
            'is_booked': False
        }
        form = WeeklyTimeSlotForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)

    def test_booking_form_clean_appointment_datetime_valid(self):
        future_time = datetime.now() + timedelta(days=1)
        form = BookingForm(data={'notes': 'Test note'})
        form.cleaned_data = {'appointment_datetime': future_time}
        self.assertEqual(form.clean_appointment_datetime(), future_time)

    def test_booking_form_clean_appointment_datetime_invalid(self):
        past_time = datetime.now() - timedelta(days=1)
        form = BookingForm(data={'notes': 'Test note'})
        form.cleaned_data = {'appointment_datetime': past_time}
        with self.assertRaises(Exception) as context:
            form.clean_appointment_datetime()
        self.assertIn("Appointment cannot be in the past", str(context.exception))
