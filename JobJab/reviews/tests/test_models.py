from django.test import TestCase
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db.utils import IntegrityError as DjangoIntegrityError
from django.utils import timezone

from JobJab.reviews.models import WebsiteReview, UserReview, ProviderReview
from JobJab.services.models import ServiceListing
from JobJab.core.models import CustomUser, UserChoices


class ReviewModelTests(TestCase):

    def setUp(self):
        self.reviewer = CustomUser.objects.create_user(username='reviewer', password='testpass', user_type=UserChoices.SEEKER, email='reviewer@gmail.com')
        self.reviewee = CustomUser.objects.create_user(username='reviewee', password='testpass', user_type=UserChoices.SEEKER, email='reviewee@gmail.com')
        self.provider = CustomUser.objects.create_user(username='provider', password='testpass', user_type=UserChoices.PROVIDER, email='provider@gmail.com')

        self.service = ServiceListing.objects.create(
            provider=self.provider,
            title='Test Service',
            description='Test Description',
            price=100
        )

    def test_website_review_creation(self):
        review = WebsiteReview.objects.create(
            reviewer=self.reviewer,
            rating=4,
            main_caption="Great platform",
            comment="Really enjoyed using it!"
        )
        self.assertEqual(str(review), f"Website review by {self.reviewer.username}")
        self.assertEqual(review.likes, 0)
        self.assertEqual(review.dislikes, 0)

    def test_user_review_creation_valid(self):
        review = UserReview(
            reviewer=self.reviewer,
            reviewee=self.reviewee,
            rating=5,
            main_caption="Awesome user",
            comment="Had a great experience."
        )
        review.clean()
        review.save()
        self.assertEqual(review.reviewer, self.reviewer)
        self.assertEqual(review.reviewee, self.reviewee)

    def test_user_review_cannot_review_self(self):
        review = UserReview(
            reviewer=self.reviewer,
            reviewee=self.reviewer,
            rating=1,
            main_caption="Bad user",
            comment="Don't like myself."
        )
        with self.assertRaises(ValidationError):
            review.clean()

    def test_user_review_save_without_reviewer_or_reviewee_raises(self):
        review = UserReview(rating=5, main_caption="Test", comment="Test")
        with self.assertRaises(ValueError):
            review.save()

    def test_provider_review_creation_valid(self):
        review = ProviderReview(
            reviewer=self.reviewer,
            provider=self.provider,
            rating=5,
            main_caption="Top Provider",
            comment="Excellent service"
        )
        review.clean()
        review.save()
        self.assertIn("Provider review for", str(review))

    def test_provider_review_with_invalid_service_raises(self):
        wrong_service = ServiceListing.objects.create(
            provider=self.reviewee,
            title='Wrong Service',
            description='Invalid',
            price=50
        )
        review = ProviderReview(
            reviewer=self.reviewer,
            provider=self.provider,
            service=wrong_service,
            rating=3,
            main_caption="Meh",
            comment="Not great"
        )
        with self.assertRaises(ValidationError):
            review.clean()

    def test_provider_review_cannot_review_self(self):
        review = ProviderReview(
            reviewer=self.provider,
            provider=self.provider,
            rating=4,
            main_caption="Reviewing myself",
            comment="Conflicted."
        )
        with self.assertRaises(ValidationError):
            review.clean()

    def test_provider_review_with_service_constraint(self):

        ProviderReview.objects.create(
            reviewer=self.reviewer,
            provider=self.provider,
            service=self.service,
            rating=4,
            main_caption="Great",
            comment="All good"
        )
        with self.assertRaises(DjangoIntegrityError):
            ProviderReview.objects.create(
                reviewer=self.reviewer,
                provider=self.provider,
                service=self.service,
                rating=4,
                main_caption="Duplicate",
                comment="Should fail"
            )

    def test_provider_review_without_service_constraint(self):
        ProviderReview.objects.create(
            reviewer=self.reviewer,
            provider=self.provider,
            rating=5,
            main_caption="Nice",
            comment="Just reviewing provider"
        )
        with self.assertRaises(DjangoIntegrityError):
            ProviderReview.objects.create(
                reviewer=self.reviewer,
                provider=self.provider,
                rating=3,
                main_caption="Again",
                comment="Should also fail"
            )

    def test_provider_review_with_different_service_allows_multiple(self):
        service2 = ServiceListing.objects.create(
            provider=self.provider,
            title="Service 2",
            description="Another one",
            price=150
        )
        ProviderReview.objects.create(
            reviewer=self.reviewer,
            provider=self.provider,
            service=self.service,
            rating=5,
            main_caption="First",
            comment="Nice!"
        )
        ProviderReview.objects.create(
            reviewer=self.reviewer,
            provider=self.provider,
            service=service2,
            rating=4,
            main_caption="Second",
            comment="Still nice!"
        )
        self.assertEqual(ProviderReview.objects.filter(provider=self.provider).count(), 2)
