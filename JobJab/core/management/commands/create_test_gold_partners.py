import uuid

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from JobJab.subscriptions.models import Subscription, SubscriptionChoices


class Command(BaseCommand):
    help = 'Creates test users and reviews'

    def handle(self, *args, **options):
        CustomUser = get_user_model()

        # Create test users
        test_users = []
        for i in range(1, 6):
            user = CustomUser.objects.create_user(
                username=f'partner{i}',
                email=f'partner{i}@example.com',
                password='partnerpass123',
                first_name=f'partner{i}',
                last_name=f'partner{i}',
                user_type='Provider'
            )
            test_users.append(user)
            self.stdout.write(self.style.SUCCESS(f'Created user: {user.username}'))

        for i, user in enumerate(test_users):
            Subscription.objects.create(
                user=user,
                stripe_customer_id=f"cus_test_{uuid.uuid4().hex[:10]}",
                subscription_plan_type=SubscriptionChoices.Elite.value,
            )
            self.stdout.write(self.style.SUCCESS(f'Created review for {user.username}'))