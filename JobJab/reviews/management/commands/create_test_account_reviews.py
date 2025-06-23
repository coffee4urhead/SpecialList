from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from JobJab.reviews.models import UserReview
from datetime import datetime, timedelta
import random
from faker import Faker


class Command(BaseCommand):
    help = 'Creates user reviews from other users as feedback for the account'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reviewee-username',
            type=str,
            default='Ivcho2',
            help='Username that will receive the reviews'
        )
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of reviews to generate'
        )

    def handle(self, *args, **options):
        CustomUser = get_user_model()
        fake = Faker()

        # Get users
        reviewee = CustomUser.objects.get(username=options['reviewee_username'])
        reviewers = CustomUser.objects.exclude(username=options['reviewee_username'])

        # Limit reviewers to the requested count
        reviewers = reviewers.order_by('?')[:options['count']]  # Random selection

        # Generate realistic reviews with Faker
        for i, user in enumerate(reviewers):
            # Generate different types of reviews
            if random.random() < 0.2:  # 20% chance of negative review
                comment = fake.sentence(nb_words=10, variable_nb_words=True) + " " + random.choice([
                    "Would not recommend.",
                    "Very disappointing experience.",
                    "Avoid at all costs.",
                    "Terrible service."
                ])
                rating = random.randint(1, 2)
            else:
                comment = fake.sentence(nb_words=15, variable_nb_words=True) + " " + random.choice([
                    "Highly recommended!",
                    "Excellent experience.",
                    "Will definitely use again.",
                    "Very professional."
                ])
                rating = random.randint(3, 5)

            UserReview.objects.create(
                reviewer=user,
                reviewee=reviewee,
                rating=rating,
                main_caption=f"Review about {reviewee.username}",
                comment=comment,
                likes=random.randint(0, 50),
                dislikes=random.randint(0, 10),
                created_at=datetime.now() - timedelta(days=random.randint(0, 365))
            )

            self.stdout.write(self.style.SUCCESS(
                f'Created review #{i + 1} for {reviewee.username} from {user.username}'
            ))

            self.stdout.write(self.style.SUCCESS(
                f'Successfully created {len(reviewers)} reviews for {reviewee.username}'
            ))