from django.db import models
from django.conf import settings

class SubscriptionChoices(models.TextChoices):
    Starter = 'Starter', 'Starter'
    Growth = 'Growth', 'Growth'
    Elite = 'Elite', 'Elite'

class Subscription(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription'
    )
    stripe_customer_id = models.CharField(max_length=255, unique=True)
    stripe_subscription_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    subscription_plan_type = models.CharField(choices=SubscriptionChoices, default=SubscriptionChoices.Starter)
    subscription_plan_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)

    current_period_start = models.DateTimeField(blank=True, null=True)
    current_period_end = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Subscription for {self.user.username} - Status: {self.status}"
