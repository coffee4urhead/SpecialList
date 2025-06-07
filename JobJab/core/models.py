from django.contrib.auth.models import AbstractUser
from JobJab.settings import AUTH_USER_MODEL
from django.db import models
import pytz

TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.all_timezones]

class UserChoices(models.TextChoices):
    Seeker = "Seeker" "Seeker"
    Provider = "Provider" "Provider"

class Certificate(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates')
    image = models.ImageField(upload_to='certificates/')
    title = models.CharField(max_length=100, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title or 'Certificate'}"

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


class CustomUser(AbstractUser):
    user_type = models.CharField(choices=UserChoices)
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, default='profile_pics/avatar-default-photo.png')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profession = models.CharField(max_length=100, blank=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    timezone = models.CharField (
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default='UTC',
        help_text='User timezone, e.g., America/New_York'
    )
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    def __str__(self):
        return f"{ self.username } - {self.first_name} {self.last_name}"

