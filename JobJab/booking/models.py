from datetime import datetime, timedelta

from django.db import models
from django.conf import settings
from JobJab.core.models import UserChoices
from JobJab.services.models import ServiceListing


class BookingStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    CANCELED = 'canceled', 'Canceled'
    COMPLETED = 'completed', 'Completed'


class ProviderAvailability(models.Model):
    provider = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='availability',
        limit_choices_to={'user_type': UserChoices.Provider}
    )
    slot_duration = models.PositiveIntegerField(
        default=30,
        help_text="Duration of each time slot in minutes (e.g., 30, 60)"
    )
    buffer_time = models.PositiveIntegerField(
        default=15,
        help_text="Buffer time between appointments (minutes)"
    )
    is_active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.time_slots.exists():
            self._generate_weekly_slots()

    def _generate_weekly_slots(self):
        for day in range(5):
            current_time = self.provider.preferred_start
            while current_time < self.provider.preferred_end:
                end_time = (datetime.combine(datetime.today(), current_time) +
                            timedelta(minutes=self.slot_duration)).time()

                WeeklyTimeSlot.objects.create(
                    availability=self,
                    day_of_week=day,
                    start_time=current_time,
                    end_time=end_time,
                    is_booked=False
                )
                current_time = (datetime.combine(datetime.today(), end_time) +
                                timedelta(minutes=self.buffer_time)).time()

    def __str__(self):
        return f"Availability for {self.provider}"


class WeeklyTimeSlot(models.Model):
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
    ]

    availability = models.ForeignKey(
        ProviderAvailability,
        on_delete=models.CASCADE,
        related_name='time_slots'
    )
    day_of_week = models.PositiveSmallIntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        unique_together = ('availability', 'day_of_week', 'start_time')

    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


class Booking(models.Model):
    seeker = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings_made',
        limit_choices_to={'user_type': UserChoices.Seeker}
    )
    provider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='bookings_received',
        limit_choices_to={'user_type': UserChoices.Provider}
    )
    service = models.ForeignKey(ServiceListing, on_delete=models.CASCADE, related_name='bookings')

    appointment_datetime = models.DateTimeField()
    status = models.CharField(
        max_length=10,
        choices=BookingStatus,
        default=BookingStatus.PENDING
    )
    notes = models.TextField(blank=True)
    time_slot = models.ForeignKey(
        WeeklyTimeSlot,
        on_delete=models.CASCADE,
        related_name='bookings',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking {self.id} from {self.seeker} to {self.provider} at {self.appointment_datetime}"
