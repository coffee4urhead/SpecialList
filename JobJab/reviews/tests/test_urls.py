from django.test import TestCase
from django.urls import reverse, resolve
from JobJab.reviews.views import (
    LeaveUserReviewView,
    EditUserReviewView,
    DeleteUserReviewView
)
from JobJab.core.models import CustomUser, UserChoices
from JobJab.reviews.models import UserReview


class UserReviewURLTests(TestCase):

    def setUp(self):
        self.reviewer = CustomUser.objects.create_user(username="john", password="pass123", user_type=UserChoices.SEEKER, email="reviewer@gmail.com")
        self.reviewee = CustomUser.objects.create_user(username="jane", password="pass123", user_type=UserChoices.PROVIDER, email="reviewee@gmail.com")
        self.review = UserReview.objects.create(
            reviewer=self.reviewer,
            reviewee=self.reviewee,
            rating=5,
            main_caption="Great",
            comment="Excellent work"
        )


    def test_leave_review_url_resolves(self):
        url = reverse("leave_review", kwargs={"username": self.reviewee.username})
        expected_url = f"/reviews/user/{self.reviewee.username}/leaveReview/"
        self.assertEqual(url, expected_url)
        self.assertEqual(resolve(url).func.view_class, LeaveUserReviewView)

    def test_edit_review_url_resolves(self):
        url = reverse("edit_user_review", kwargs={"username": self.reviewee.username, "review_id": self.review.id})
        self.assertEqual(url, f"/reviews/user/{self.reviewee.username}/editReview/{self.review.id}/")
        self.assertEqual(resolve(url).func.view_class, EditUserReviewView)

    def test_delete_review_url_resolves(self):
        url = reverse("delete_user_review", kwargs={"username": self.reviewee.username, "review_id": self.review.id})
        self.assertEqual(resolve(url).func.view_class, DeleteUserReviewView)


    def test_leave_review_requires_authentication(self):
        url = reverse("leave_review", kwargs={"username": self.reviewee.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_edit_review_requires_authentication(self):
        url = reverse("edit_user_review", kwargs={"username": self.reviewee.username, "review_id": self.review.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_delete_review_requires_authentication(self):
        url = reverse("delete_user_review", kwargs={"username": self.reviewee.username, "review_id": self.review.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user_can_access_leave_review(self):
        self.client.login(username="john", password="pass123")
        url = reverse("leave_review", kwargs={"username": self.reviewee.username})
        response = self.client.get(url)
        self.assertIn(response.status_code, [200, 302])

