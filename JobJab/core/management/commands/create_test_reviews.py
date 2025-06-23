from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from JobJab.reviews.models import ReviewType, WebsiteReview
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Creates test users and reviews'

    def handle(self, *args, **options):
        CustomUser = get_user_model()

        # Create test users
        test_users = []
        for i in range(1, 6):
            user = CustomUser.objects.create_user(
                username=f'testuser{i}',
                email=f'test{i}@example.com',
                password='testpass123',
                first_name=f'Test{i}',
                last_name=f'User{i}',
                user_type='Seeker' if i % 2 else 'Provider'
            )
            test_users.append(user)
            self.stdout.write(self.style.SUCCESS(f'Created user: {user.username}'))

        # Create test reviews
        review_texts = [
            "Great platform, found exactly what I needed!",
            "Easy to use and very intuitive interface",
            "Had some issues at first but support helped quickly",
            "Best service marketplace I've used",
            "Could improve search functionality"
        ]

        for i, user in enumerate(test_users):
            WebsiteReview.objects.create(
                reviewer=user,
                rating=random.randint(3, 5),
                main_caption=f"Review {i+1}",
                comment=review_texts[i],
                created_at=datetime.now() - timedelta(days=i)
            )
            self.stdout.write(self.style.SUCCESS(f'Created review for {user.username}'))