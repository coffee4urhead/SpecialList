import os

from PIL import Image
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator, MinLengthValidator

from django.db import models
from pdf2image import convert_from_path

from JobJab import settings
from JobJab.settings import AUTH_USER_MODEL
import pytz

TIMEZONE_CHOICES = [(tz, tz) for tz in pytz.all_timezones]


class Organization(models.Model):
    name = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='organization_logos/', default='static/images/default-org.jpg',
                             validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])],
                             blank=True, null=True)
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
    user = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificates'
    )
    title = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Title of the certificate (e.g., 'Python Developer Certification')",
        validators=[MinLengthValidator(10, message="Certificate title is too short")],
    )
    certificate_file = models.FileField(
        upload_to='certificates/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'], message="Certificate file should be a PDF")],
        help_text="Upload PDF certificate file",
        blank=True,
        null=True,
    )
    preview_image = models.ImageField(
        upload_to='certificate_previews/',
        blank=True,
        null=True
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(
        default=False,
        help_text="Mark if the certificate has been verified by admin"
    )

    def generate_preview(self):
        if self.certificate_file and not self.preview_image:
            poppler_local_path = r'D:\Poppler\poppler-24.08.0\Library\bin'

            images = convert_from_path(
                self.certificate_file.path,
                poppler_path=poppler_local_path
            )

            if images:
                rgb_images = [img.convert('RGB') for img in images]

                total_height = sum(img.height for img in rgb_images)
                max_width = max(img.width for img in rgb_images)

                combined_image = Image.new('RGB', (max_width, total_height), (255, 255, 255))

                y_offset = 0
                for img in rgb_images:
                    combined_image.paste(img, (0, y_offset))
                    y_offset += img.height

                img_path = os.path.join(settings.MEDIA_ROOT, 'certificate_previews', f'preview_{self.id}.jpg')
                os.makedirs(os.path.dirname(img_path), exist_ok=True)
                combined_image.save(img_path, 'JPEG', quality=85)

                self.preview_image.name = os.path.join('certificate_previews', f'preview_{self.id}.jpg')
                self.save()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.certificate_file and not self.preview_image:
            self.generate_preview()

    class Meta:
        verbose_name = "Certificate"
        verbose_name_plural = "Certificates"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.user.username} - {self.title or 'Certificate'}"

    @property
    def filename(self):
        return self.certificate_file.name.split('/')[-1]

    def get_absolute_url(self):
        return self.certificate_file.url


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

    backcover_profile = models.ImageField(upload_to='profiles/', validators=[
        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])], blank=True,
                                          default='profiles/default-backcover.jpg')
    profile_picture = models.ImageField(upload_to='profile_pics/', validators=[
        FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])], blank=True,
                                        default='profile_pics/avatar-default-photo.png')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profession = models.CharField(max_length=100, blank=True)
    personal_number = models.CharField(max_length=100, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    timezone = models.CharField(
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default='UTC',
        help_text='User timezone, e.g., America/New_York'
    )

    def get_user_followers(self):
        return self.followers.all().count()

    def get_user_following(self):
        return self.following.all().count()

    def __str__(self):
        return f"{self.username} - {self.first_name} {self.last_name}"


class UserLocation(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s location"
