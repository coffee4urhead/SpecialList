from datetime import time
from django.test import TestCase
from django.contrib.auth import get_user_model
from JobJab.booking.models import ProviderAvailability, WeeklyTimeSlot, Booking, BookingStatus
from JobJab.services.models import ServiceListing
from JobJab.core.models import UserChoices

User = get_user_model()


class BookingModelsTest(TestCase):
    def setUp(self):
        self.provider = User.objects.create_user(
            username='provider1',
            password='pass',
            email='provider@gmail.com',
            user_type=UserChoices.PROVIDER,
            preferred_start=time(9, 0),
            preferred_end=time(17, 0),
        )
        self.seeker = User.objects.create_user(
            username='seeker1',
            password='pass',
            email='seeker@gmail.com',
            user_type=UserChoices.SEEKER,
        )
        self.service = ServiceListing.objects.create(
            provider=self.provider,
            title='Test Service',
            price=50.00,
        )

    def test_provider_availability_and_slot_generation(self):
        availability = ProviderAvailability.objects.create(provider=self.provider)
        slots = availability.time_slots.all()
        self.assertTrue(slots.exists())
        self.assertEqual(slots.values_list('day_of_week', flat=True).distinct().count(), 5)
        self.assertTrue(all(slot.availability == availability for slot in slots))

    def test_weekly_time_slot_unique_constraint(self):
        availability = ProviderAvailability.objects.create(provider=self.provider)
        availability.time_slots.all().delete()

        slot1 = WeeklyTimeSlot.objects.create(
            availability=availability,
            day_of_week=0,
            start_time=time(9, 0),
            end_time=time(9, 30),
            is_booked=False,
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            WeeklyTimeSlot.objects.create(
                availability=availability,
                day_of_week=0,
                start_time=time(9, 0),
                end_time=time(10, 0),
                is_booked=False,
            )

    def test_weekly_time_slot_change_status(self):
        availability = ProviderAvailability.objects.create(provider=self.provider)
        slot = WeeklyTimeSlot.objects.create(
            availability=availability,
            day_of_week=1,
            start_time=time(10, 0),
            end_time=time(10, 30),
            is_booked=False,
        )
        slot.change_status(True)
        slot.refresh_from_db()
        self.assertTrue(slot.is_booked)

    def test_booking_creation_and_str(self):
        availability = ProviderAvailability.objects.create(provider=self.provider)
        slot = WeeklyTimeSlot.objects.filter(availability=availability).first()
        booking = Booking.objects.create(
            seeker=self.seeker,
            provider=self.provider,
            service=self.service,
            appointment_datetime='2025-08-10T10:00:00Z',
            status=BookingStatus.PENDING,
            notes='Please be on time',
            time_slot=slot,
            price=self.service.price,
        )
        self.assertEqual(str(booking),
                         f"Booking {booking.id} from {self.seeker} to {self.provider} at {booking.appointment_datetime}")
        self.assertEqual(booking.status, BookingStatus.PENDING)
        self.assertEqual(booking.price, self.service.price)
