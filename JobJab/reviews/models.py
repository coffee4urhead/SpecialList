from django.core.exceptions import ValidationError

from JobJab.settings import AUTH_USER_MODEL
from JobJab.services.models import ServiceListing
from JobJab.core.models import UserChoices
from django.db import models

class ReviewType(models.TextChoices):
    PROVIDER = 'provider', 'Service Provider Review'
    SERVICE = 'service', 'Specific Service Review'
    WEBSITE = 'website', 'Website/Platform Review'

class Review(models.Model):
    reviewer = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='given_reviews')
    review_type = models.CharField(
        max_length=10,
        choices=ReviewType,
        default=ReviewType.WEBSITE
    )
    service = models.ForeignKey(ServiceListing, on_delete=models.CASCADE, related_name='reviews', null=True, blank=True)
    provider = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='provider_reviews',
        null=True,
        blank=True,
        limit_choices_to={'user_type': UserChoices.Provider}
    )
    likes = models.IntegerField(default=0)
    dislikes = models.IntegerField(default=0)
    rating = models.SmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    main_caption = models.CharField(max_length=100)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    #Adding a constraint or logic to prevent multiple reviews by the same reviewer on the same service/booking would improve data quality.

    def clean(self):
        super().clean()

        if self.review_type == ReviewType.PROVIDER and not self.provider:
            raise ValidationError("Provider reviews must have a provider specified")

        if self.review_type == ReviewType.SERVICE and not self.service:
            raise ValidationError("Service reviews must have a service specified")

        if self.review_type == ReviewType.WEBSITE and (self.provider or self.service):
            raise ValidationError("Website reviews shouldn't have provider or service specified")

    class Meta:
        constraints = [
            # Ensure only one relationship is set based on review_type
            models.CheckConstraint(
                check=(
                        models.Q(review_type=ReviewType.PROVIDER, provider__isnull=False, service__isnull=True) |
                        models.Q(review_type=ReviewType.SERVICE, service__isnull=False, provider__isnull=True) |
                        models.Q(review_type=ReviewType.WEBSITE, provider__isnull=True, service__isnull=True)
                ),
                name='consistent_review_type'
            )
        ]

    def __str__(self):
        if self.review_type == ReviewType.PROVIDER:
            return f"Provider review for {self.provider.username} by {self.reviewer.username}"
        elif self.review_type == ReviewType.SERVICE:
            return f"Service review for {self.service.title} by {self.reviewer.username}"
        else:
            return f"Website review by {self.reviewer.username}"