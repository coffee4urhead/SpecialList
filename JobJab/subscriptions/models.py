from django.db import models
from django.conf import settings
from django.utils import timezone

class SubscriptionPlan(models.TextChoices):
    STARTER = 'Starter', 'Starter'
    GROWTH = 'Growth', 'Growth'
    ELITE = 'Elite', 'Elite'

class SubscriptionStatus(models.TextChoices):
    ACTIVE = 'active', 'Active'
    PAST_DUE = 'past_due', 'Past Due'
    UNPAID = 'unpaid', 'Unpaid'
    CANCELED = 'canceled', 'Canceled'
    INCOMPLETE = 'incomplete', 'Incomplete'
    INCOMPLETE_EXPIRED = 'incomplete_expired', 'Incomplete Expired'
    TRIALING = 'trialing', 'Trialing'

class Subscription(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    stripe_customer_id = models.CharField(max_length=255, unique=True)
    stripe_subscription_id = models.CharField(
        max_length=255,
        unique=True,
        blank=True,
        null=True,
        help_text="The Stripe subscription ID"
    )
    plan = models.CharField(
        max_length=20,
        choices=SubscriptionPlan,
        default=SubscriptionPlan.STARTER,
        help_text="The subscription plan type"
    )
    status = models.CharField(
        max_length=20,
        choices=SubscriptionStatus,
        blank=True,
        null=True,
        help_text="The current status of the subscription"
    )
    cancel_at_period_end = models.BooleanField(
        default=False,
        help_text="Whether the subscription is scheduled to cancel at period end"
    )
    current_period_start = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Start of the current billing period"
    )
    current_period_end = models.DateTimeField(
        blank=True,
        null=True,
        help_text="End of the current billing period"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s {self.get_plan_display()} Subscription ({self.get_status_display()})"

    @property
    def is_active(self):
        """Check if subscription is currently active"""
        return self.status in [
            SubscriptionStatus.ACTIVE,
            SubscriptionStatus.TRIALING
        ] and (self.current_period_end is None or self.current_period_end > timezone.now())

    class Meta:
        ordering = ['-created_at']