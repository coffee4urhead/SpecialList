from django.core.exceptions import ValidationError

from JobJab.settings import AUTH_USER_MODEL
from JobJab.services.models import ServiceListing
from JobJab.core.models import UserChoices
from django.db import models

class ReviewType(models.TextChoices):
    PROVIDER = 'provider', 'Service Provider Review'
    SERVICE = 'service', 'Specific Service Review'
    WEBSITE = 'website', 'Website/Platform Review'

class BaseReview(models.Model):
    reviewer = models.ForeignKey(AUTH_USER_MODEL, blank=True, null=True, on_delete=models.CASCADE)
    rating = models.SmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    main_caption = models.CharField(max_length=40)
    comment = models.TextField(max_length=300)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)

    class Meta:
        abstract = True


class WebsiteReview(BaseReview):
    """Review for the entire platform"""

    def __str__(self):
        return f"Website review by {self.reviewer.username}"


class UserReview(BaseReview):
    """Review for a specific user account"""
    reviewee = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='user_reviews'
    )

    def clean(self):
        # Only validate if both reviewer and reviewee are set
        if self.reviewer_id and self.reviewee_id:
            if self.reviewer_id == self.reviewee_id:
                raise ValidationError("Cannot review yourself")

    def save(self, *args, **kwargs):
        """Ensure required fields are set before saving"""
        if not hasattr(self, 'reviewer'):
            raise ValueError("Reviewer must be set before saving")
        if not hasattr(self, 'reviewee'):
            raise ValueError("Reviewee must be set before saving")
        super().save(*args, **kwargs)


class ProviderReview(BaseReview):
    """Review for a service provider"""
    provider = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='provider_reviews',
        limit_choices_to={'user_type': UserChoices.PROVIDER}
    )
    service = models.ForeignKey(
        ServiceListing,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='service_reviews'
    )

    def clean(self):
        if not self.reviewer:
            raise ValidationError("Provider reviews must have a reviewer")
        if not self.provider:
            raise ValidationError("Provider reviews must have a provider")
        if self.reviewer == self.provider:
            raise ValidationError("Cannot review yourself")
        if self.service and self.service.provider != self.provider:
            raise ValidationError("Service must belong to the provider being reviewed")

    def __str__(self):
        if self.service:
            return f"Service review for {self.service.title} by {self.reviewer.username}"
        return f"Provider review for {self.provider.username} by {self.reviewer.username}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['reviewer', 'provider', 'service'],
                name='unique_provider_service_review',
                condition=models.Q(service__isnull=False)
            ),
            models.UniqueConstraint(
                fields=['reviewer', 'provider'],
                name='unique_provider_review',
                condition=models.Q(service__isnull=True)
            )
        ]