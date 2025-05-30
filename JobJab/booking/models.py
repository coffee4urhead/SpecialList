from django.db import models
from django.conf import settings
from JobJab.core.models import UserChoices
from JobJab.services.models import ServiceListing

class BookingStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    CONFIRMED = 'confirmed', 'Confirmed'
    CANCELED = 'canceled', 'Canceled'
    COMPLETED = 'completed', 'Completed'

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

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Booking {self.id} from {self.seeker} to {self.provider} at {self.appointment_datetime}"
