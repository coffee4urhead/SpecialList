from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import random
from faker import Faker

User = get_user_model()
fake = Faker()


class Command(BaseCommand):
    help = 'Populates users with followers and following relationships'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=20,
            help='Number of users to create'
        )
        parser.add_argument(
            '--max-follows',
            type=int,
            default=5,
            help='Maximum number of follows per user'
        )
        parser.add_argument(
            '--target-user',
            type=str,
            help='Specific username to add followers/following to'
        )

    def handle(self, *args, **options):
        num_users = options['users']
        max_follows = options['max_follows']
        target_username = options['target_user']

        if target_username:
            target_user, created = User.objects.get_or_create(
                username=target_username,
                defaults={
                    'email': f'{target_username}@example.com',
                    'password': 'testpass123',
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created target user: {target_user}'))
        else:
            target_user = None

        users = []
        for i in range(num_users):
            user, created = User.objects.get_or_create(
                username=f'user_{i}',
                defaults={
                    'email': f'user_{i}@example.com',
                    'password': 'testpass123',
                    'first_name': fake.first_name(),
                    'last_name': fake.last_name(),
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created user: {user}'))
            users.append(user)

        for user in users:
            num_follows = random.randint(1, max_follows)

            users_to_follow = random.sample(
                [u for u in users if u != user],
                min(num_follows, len(users) - 1)
            )

            for followed_user in users_to_follow:
                user.following.add(followed_user)
                followed_user.followers.add(user)
                self.stdout.write(f'{user} now follows {followed_user}')

            if target_user and user != target_user and random.random() > 0.7:
                user.following.add(target_user)
                target_user.followers.add(user)
                self.stdout.write(f'{user} now follows target user {target_user}')

        self.stdout.write(self.style.SUCCESS(
            f'Successfully created {num_users} users with follow relationships'
        ))

# Basic usage - creates 20 users with up to 5 follows each
#python manage.py populate_follows

# Create 50 users with up to 10 follows each
#python manage.py populate_follows --users 50 --max-follows 10

# Add followers/following to a specific existing user
#python manage.py populate_follows --target-user yourusername