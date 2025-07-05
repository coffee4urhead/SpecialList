from django.db import models
from django.conf import settings

from JobJab.core.models import UserChoices
from JobJab.settings import AUTH_USER_MODEL


class AvailabilityType(models.TextChoices):
    AVAILABLE = 'available', 'Available'
    UNAVAILABLE = 'unavailable', 'Unavailable'


class Availability(models.Model):
    provider = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': UserChoices.Provider},
        related_name='availabilities'
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=12,
        choices=AvailabilityType,
        default=AvailabilityType.AVAILABLE
    )
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.provider} - {self.status} on {self.date} from {self.start_time} to {self.end_time}"

class ServiceCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class ServiceListing(models.Model):
    provider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='services')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    service_photo = models.ImageField(upload_to='services/photos', blank=True)
    category = models.ForeignKey(ServiceCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='services')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.PositiveIntegerField(default=60)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.provider.username}"
