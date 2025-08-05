from django.test import TestCase
from django.core.exceptions import ValidationError

from JobJab.reviews.forms import UserReviewForm, WebsiteReviewForm
from JobJab.reviews.models import UserReview, WebsiteReview
from JobJab.core.models import CustomUser, UserChoices


class ReviewFormTests(TestCase):

    def setUp(self):
        self.reviewer = CustomUser.objects.create_user(
            username="reviewer", password="testpass", user_type=UserChoices.SEEKER, email="reviewer@gmail.com"
        )
        self.reviewee = CustomUser.objects.create_user(
            username="reviewee", password="testpass", user_type=UserChoices.PROVIDER,  email="reviewee@gmail.com"
        )


    def test_user_review_form_valid(self):
        form_data = {
            "rating": 5,
            "main_caption": "Great experience",
            "comment": "Highly recommend!"
        }
        form = UserReviewForm(
            data=form_data,
            reviewer=self.reviewer,
            reviewee=self.reviewee
        )
        self.assertTrue(form.is_valid())
        review = form.save()
        self.assertEqual(review.reviewer, self.reviewer)
        self.assertEqual(review.reviewee, self.reviewee)

    def test_user_review_form_missing_reviewer(self):
        form_data = {
            "rating": 4,
            "main_caption": "Nice",
            "comment": "Good job"
        }
        form = UserReviewForm(data=form_data, reviewee=self.reviewee)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertIn("Reviews must have a reviewer", str(form.errors["__all__"]))

    def test_user_review_form_missing_reviewee(self):
        form_data = {
            "rating": 3,
            "main_caption": "Decent",
            "comment": "Okay service"
        }
        form = UserReviewForm(data=form_data, reviewer=self.reviewer)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertIn("Reviews must have a reviewee", str(form.errors["__all__"]))

    def test_user_review_form_cannot_review_self(self):
        form_data = {
            "rating": 2,
            "main_caption": "Self Review",
            "comment": "Can't do this"
        }
        form = UserReviewForm(data=form_data, reviewer=self.reviewer, reviewee=self.reviewer)
        self.assertFalse(form.is_valid())
        self.assertIn("Cannot review yourself", str(form.errors["__all__"]))

    def test_user_review_form_reviewee_display_field(self):
        form = UserReviewForm(reviewer=self.reviewer, reviewee=self.reviewee)
        self.assertIn("reviewee_display", form.fields)
        self.assertEqual(form.fields["reviewee_display"].widget.attrs.get("readonly"), "readonly")
        self.assertEqual(form.fields["reviewee_display"].initial, str(self.reviewee))


    def test_website_review_form_valid(self):
        form_data = {
            "rating": 5,
            "main_caption": "Excellent platform",
            "comment": "Loved using this service!"
        }
        form = WebsiteReviewForm(data=form_data, reviewer=self.reviewer)
        self.assertTrue(form.is_valid())
        review = form.save()
        self.assertEqual(review.reviewer, self.reviewer)
        self.assertIsInstance(review, WebsiteReview)

    def test_website_review_form_missing_reviewer(self):
        form_data = {
            "rating": 4,
            "main_caption": "Good site",
            "comment": "Nice work"
        }
        form = WebsiteReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)
        self.assertIn("You must be logged in to leave a review", str(form.errors["__all__"]))

    def test_website_review_form_widget_attributes(self):
        form = WebsiteReviewForm(reviewer=self.reviewer)
        self.assertEqual(form.fields["comment"].widget.attrs["rows"], 4)
        self.assertIn("placeholder", form.fields["comment"].widget.attrs)
        self.assertEqual(form.fields["main_caption"].widget.attrs["maxlength"], "40")
        self.assertEqual(form.fields["rating"].widget.attrs["min"], 1)
        self.assertEqual(form.fields["rating"].widget.attrs["max"], 5)
