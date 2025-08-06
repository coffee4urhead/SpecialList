import os
from datetime import time

from PIL import Image
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator, MinLengthValidator, MaxValueValidator, MinValueValidator

from django.db import models
from django.urls import reverse
from django.utils import timezone
from pdf2image import convert_from_path

from JobJab import settings
from JobJab.services.models import ServiceListing
from JobJab.settings import AUTH_USER_MODEL
from JobJab.core.choices import UserChoices
import pytz

from JobJab.core.model_managers import UnreadNotificationManager
from JobJab.subscriptions.models import Subscription

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


class CustomUser(AbstractUser):
    user_type = models.CharField(max_length=20, choices=UserChoices, default=UserChoices.SEEKER)
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
    preferred_start = models.TimeField(blank=True, null=True, default=time(9, 0))
    preferred_end = models.TimeField(blank=True, null=True, default=time(17, 0))
    is_verified = models.BooleanField(default=False)
    verified_at = models.DateTimeField(blank=True, null=True)
    subscription_membership = models.OneToOneField(Subscription, on_delete=models.CASCADE, blank=True, null=True,
                                                   related_name='user_subscription')

    chat_bubble_color = models.CharField(max_length=7, default="#32AE88")
    chat_bubble_shape = models.CharField(max_length=20, default="rounded")

    timezone = models.CharField(
        max_length=50,
        choices=TIMEZONE_CHOICES,
        default='UTC',
        help_text='User timezone, e.g., America/New_York'
    )

    @property
    def user_services(self):
        return self.services.all().count()

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


class NotificationType(models.TextChoices):
    WARNING = 'warning', 'Warning'
    BAN = 'ban', 'Ban Notice'
    REPORT = 'report', 'Report Update'
    INFO = 'info', 'Information'
    SYSTEM = 'system', 'System Message'


class Notification(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=100)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NotificationType,
        default=NotificationType.INFO
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = models.Manager()
    unread = UnreadNotificationManager()

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} notification for {self.user.username}"

    def mark_as_read(self):
        self.is_read = True
        self.save()

    @classmethod
    def create_notification(cls, user, title, message, notification_type=NotificationType.INFO, related_object=None):
        notification = cls(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type
        )

        if related_object:
            notification.related_object = related_object

        notification.save()
        return notification


class BlacklistReason(models.TextChoices):
    SPAM = 'spam', 'Spam or misleading content'
    ABUSE = 'abuse', 'Abusive or harmful content'
    INAPPROPRIATE = 'inappropriate', 'Sexually explicit content'
    HATE_SPEECH = 'hate_speech', 'Hate speech or discrimination'
    PRIVACY = 'privacy', 'Privacy violation'
    SCAM = 'scam', 'Scam or fraud'
    COPYRIGHT = 'copyright', 'Copyright infringement'
    OTHER = 'other', 'Other'


class BlacklistStatus(models.TextChoices):
    PENDING = 'pending', 'Pending Review'
    APPROVED = 'approved', 'Approved (Content Removed)'
    REJECTED = 'rejected', 'Rejected (False Report)'
    WARNING = 'warning', 'Warning Issued'
    BANNED = 'banned', 'User Banned'


class BlacklistItem(models.Model):
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reported_items'
    )

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    reason = models.CharField(
        max_length=20,
        choices=BlacklistReason.choices,
        default=BlacklistReason.OTHER
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Additional details about the report"
    )

    status = models.CharField(
        max_length=20,
        choices=BlacklistStatus,
        default=BlacklistStatus.PENDING
    )
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='moderated_items'
    )
    moderator_notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    auto_hidden = models.BooleanField(
        default=False,
        help_text="Whether the content was automatically hidden"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
        ]
        verbose_name = "Blacklist Item"
        verbose_name_plural = "Blacklist Items"

    def __str__(self):
        return f"Report on {self.content_type} #{self.object_id} - {self.get_reason_display()}"

    def clean(self):
        if hasattr(self.content_object, 'user'):
            if self.reporter and self.reporter == self.content_object.user:
                raise ValidationError("You cannot report your own content.")

        if not self.pk:
            existing = BlacklistItem.objects.filter(
                content_type=self.content_type,
                object_id=self.object_id,
                status__in=[BlacklistStatus.PENDING, BlacklistStatus.APPROVED, BlacklistStatus.WARNING]
            ).exists()
            if existing:
                raise ValidationError("This content has already been reported and is under review.")

    def save(self, *args, **kwargs):
        if self.reason in [BlacklistReason.ABUSE, BlacklistReason.HATE_SPEECH, BlacklistReason.INAPPROPRIATE]:
            self.auto_hidden = True

        super().save(*args, **kwargs)

        if self.auto_hidden:
            self.hide_content()

    def hide_content(self):
        """Hide the reported content automatically"""
        content = self.content_object

        if isinstance(content, ServiceListing):
            content.is_active = False
            content.deactivation_reason = f"Hidden due to report: {self.get_reason_display()}"
            content.save()

        elif hasattr(content, 'is_active'):
            content.is_active = False
            content.save()

    def approve_report(self, moderator, notes=None):
        """Approve the report and take appropriate action"""
        self.status = BlacklistStatus.APPROVED
        self.moderator = moderator
        self.moderator_notes = notes
        self.resolved_at = timezone.now()
        self.save()

        if self.content_type.model != 'customuser':
            if hasattr(self.content_object, 'is_active'):
                self.content_object.is_active = False
                self.content_object.save()

        self.check_user_ban()

    def reject_report(self, moderator, notes=None):
        """Reject the report as invalid"""
        self.status = BlacklistStatus.REJECTED
        self.moderator = moderator
        self.moderator_notes = notes
        self.resolved_at = timezone.now()
        self.save()

        if self.auto_hidden and hasattr(self.content_object, 'is_active'):
            self.content_object.is_active = True
            self.content_object.save()

    def get_warning_message(self):
        if self.reason == BlacklistReason.SCAM:
            return f"""
            Warning: This {self.content_type.model} has been reported for potential scam activity.

            Report details:
            - Reason: {self.get_reason_display()}
            - Description: {self.description}
            - Reported by: {self.reporter.username}
            - Date: {self.created_at.strftime('%Y-%m-%d %H:%M')}

            Please proceed with caution.
            """
        return None

    def get_content_url(self):
        if self.content_type.model == 'servicelisting':
            return reverse('extended_service_display', kwargs={'service_id': self.object_id})

        elif self.content_type.model == 'comment':
            comment = self.content_object
            service = ServiceListing.objects.filter(comments=comment).first()
            if service:
                return f"{reverse('extended_service_display', kwargs={'service_id': service.id})}#comment-{self.object_id}"
            return None

        elif self.content_type.model == 'customuser':
            return reverse('account_view', kwargs={'username': self.content_object.username})

        elif self.content_type.model == 'userreview':
            return reverse('account_view',
                           kwargs={'username': self.content_object.reviewee.username}) + f"#review-{self.object_id}"

        return None

    def check_user_ban(self, user=None):
        """Check if user should be banned based on previous reports"""
        if user is None:
            if isinstance(self.content_object, CustomUser):
                user = self.content_object
            elif hasattr(self.content_object, 'user'):
                user = self.content_object.user
            else:
                return False  # No user associated with this content

        approved_reports = BlacklistItem.objects.filter(
            content_type=ContentType.objects.get_for_model(user),
            object_id=user.id,
            status=BlacklistStatus.APPROVED
        ).exclude(pk=self.pk).count()

        if approved_reports + 1 >= 3:
            user.is_active = False
            user.save()

            self.status = BlacklistStatus.BANNED
            self.save()

            profile, _ = UserBlacklistProfile.objects.get_or_create(user=user)
            profile.is_banned = True
            profile.ban_reason = "Automatic ban after 3 approved reports"
            profile.banned_at = timezone.now()
            profile.banned_by = self.moderator
            profile.save()
            return True
        return False


class UserBlacklistProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='blacklist_profile'
    )
    is_banned = models.BooleanField(default=False)
    ban_reason = models.TextField(blank=True, null=True)
    banned_at = models.DateTimeField(blank=True, null=True)
    banned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='banned_users'
    )
    warning_count = models.PositiveIntegerField(default=0)
    last_warning = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Blacklist status for {self.user.username}"

    def issue_warning(self, moderator, reason):
        """Issue a warning to the user"""
        self.warning_count += 1
        self.last_warning = timezone.now()
        self.save()

        Notification.objects.create(
            user=self.user,
            title="Content Violation Warning",
            message=f"Your content has been flagged for violating our policies. Reason: {reason}",
            notification_type="warning"
        )

        if self.warning_count >= 3:
            self.ban_user(moderator, "Automatic ban after 3 warnings")

    def ban_user(self, moderator, reason):
        """Ban the user from the platform"""
        self.is_banned = True
        self.ban_reason = reason
        self.banned_at = timezone.now()
        self.banned_by = moderator
        self.save()

        self.user.is_active = False
        self.user.save()

        Notification.objects.create(
            user=self.user,
            title="Account Banned",
            message=f"Your account has been banned. Reason: {reason}",
            notification_type="ban"
        )

    def unban_user(self, moderator, reason):
        """Unban the user"""
        self.is_banned = False
        self.ban_reason = f"Unbanned: {reason}"
        self.save()

        self.user.is_active = True
        self.user.save()

        Notification.objects.create(
            user=self.user,
            title="Account Unbanned",
            message=f"Your account has been unbanned. Reason: {reason}",
            notification_type="info"
        )
