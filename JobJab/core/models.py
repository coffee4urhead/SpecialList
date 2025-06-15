from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator

from JobJab.settings import AUTH_USER_MODEL
from django.db import models
import pytz

TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.all_timezones]


class Organization(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='organization_logos/', blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name


class UserOrganization(models.Model):
    """Intermediate model for additional relationship data"""
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    position = models.CharField(max_length=100, blank=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'organization')


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

    followers = models.ManyToManyField(AUTH_USER_MODEL, related_name='user_followers', blank=True)
    following = models.ManyToManyField(AUTH_USER_MODEL, related_name='user_followings', blank=True)

    organizations = models.ManyToManyField(
        Organization,
        related_name='members',
        blank=True,
        through='UserOrganization'
    )

    backcover_profile = models.ImageField(upload_to='profiles/', validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])], blank=True, default='profiles/default-backcover.jpg')
    profile_picture = models.ImageField(upload_to='profile_pics/', validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])], blank=True, default='profile_pics/avatar-default-photo.png')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profession = models.CharField(max_length=100, blank=True)
    personal_number = models.CharField(max_length=100, blank=True, null=True)
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

    def get_user_followers(self):
        return self.followers.all().count()

    def get_user_following(self):
        return self.following.all().count()

    def __str__(self):
        return f"{ self.username } - {self.first_name} {self.last_name}"

