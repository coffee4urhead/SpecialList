from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from unittest.mock import patch

from JobJab.reviews.models import UserReview
from JobJab.core.models import Notification, NotificationType

User = get_user_model()

class UserReviewViewTests(TestCase):

    def setUp(self):
        self.client = Client()

        self.reviewer = User.objects.create_user(username='reviewer', password='pass123', user_type='seeker', email='reviewer@gmail.com')
        self.reviewee = User.objects.create_user(username='reviewee', password='pass123', user_type='provider', email='reviewee@gmail.com')

        self.review = UserReview.objects.create(
            reviewer=self.reviewer,
            reviewee=self.reviewee,
            rating=4,
            main_caption="Good",
            comment="Nice job"
        )

    def login_reviewer(self):
        self.client.login(username='reviewer', password='pass123')


    def test_leave_review_view_get_authenticated(self):
        self.login_reviewer()
        url = reverse('leave_review', kwargs={'username': self.reviewee.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIn('reviewee', response.context)
        self.assertEqual(response.context['reviewee'], self.reviewee)

    def test_leave_review_view_get_unauthenticated_redirects(self):
        url = reverse('leave_review', kwargs={'username': self.reviewee.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)

    def test_leave_review_view_post_valid_data_creates_review_and_notification(self):
        self.login_reviewer()
        url = reverse('leave_review', kwargs={'username': self.reviewee.username})
        data = {
            'rating': 5,
            'main_caption': 'Excellent',
            'comment': 'Great service!'
        }

        with patch.object(Notification, 'create_notification') as mock_notify:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'success', 'message': 'Review submitted successfully'})

        review = UserReview.objects.filter(reviewer=self.reviewer, reviewee=self.reviewee, main_caption='Excellent').first()
        self.assertIsNotNone(review)

        mock_notify.assert_called_once()
        args, kwargs = mock_notify.call_args
        self.assertEqual(kwargs.get('user'), self.reviewer)
        self.assertIn(str(self.reviewee), kwargs.get('title'))

    def test_leave_review_view_post_invalid_data_returns_errors(self):
        self.login_reviewer()
        url = reverse('leave_review', kwargs={'username': self.reviewee.username})
        data = {
            'rating': 6,
            'main_caption': '',
            'comment': ''
        }
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        json_response = response.json()
        self.assertEqual(json_response['status'], 'error')
        self.assertIn('rating', json_response['errors'])

    def test_leave_review_view_post_reviewer_equals_reviewee_returns_validation_error(self):
        self.login_reviewer()
        url = reverse('leave_review', kwargs={'username': self.reviewer.username})
        data = {
            'rating': 5,
            'main_caption': 'Self review',
            'comment': 'Trying to review myself'
        }
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        json_response = response.json()
        self.assertEqual(json_response['status'], 'error')
        self.assertIn('__all__', json_response['errors'])


    def test_edit_review_view_get_valid(self):
        self.login_reviewer()
        url = reverse('edit_user_review', kwargs={'username': self.reviewee.username, 'review_id': self.review.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertTrue(response.context.get('edit'))
        self.assertEqual(response.context.get('review_id'), self.review.id)

    def test_edit_review_view_get_username_mismatch(self):
        self.login_reviewer()
        url = reverse('edit_user_review', kwargs={'username': 'wrongusername', 'review_id': self.review.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(response.content, {'status': 'error', 'message': 'Username mismatch'})

    def test_edit_review_view_post_valid_update(self):
        self.login_reviewer()
        url = reverse('edit_user_review', kwargs={'username': self.reviewee.username, 'review_id': self.review.id})
        data = {
            'rating': 3,
            'main_caption': 'Updated',
            'comment': 'Updated comment'
        }
        with patch.object(Notification, 'create_notification') as mock_notify:
            response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'success', 'message': 'Review updated successfully'})

        review = UserReview.objects.get(id=self.review.id)
        self.assertEqual(review.rating, 3)
        self.assertEqual(review.main_caption, 'Updated')

        mock_notify.assert_called_once()

    def test_edit_review_view_post_invalid_data(self):
        self.login_reviewer()
        url = reverse('edit_user_review', kwargs={'username': self.reviewee.username, 'review_id': self.review.id})
        data = {
            'rating': 10,
            'main_caption': '',
            'comment': ''
        }
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        self.assertIn('rating', response.json()['errors'])

    def test_edit_review_view_post_username_mismatch(self):
        self.login_reviewer()
        url = reverse('edit_user_review', kwargs={'username': 'wrongusername', 'review_id': self.review.id})
        data = {
            'rating': 3,
            'main_caption': 'Updated',
            'comment': 'Updated comment'
        }
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 403)
        self.assertJSONEqual(response.content, {'status': 'error', 'message': 'Username mismatch'})


    def test_views_require_login(self):
        urls = [
            reverse('leave_review', kwargs={'username': self.reviewee.username}),
            reverse('edit_user_review', kwargs={'username': self.reviewee.username, 'review_id': self.review.id}),
            reverse('delete_user_review', kwargs={'username': self.reviewee.username, 'review_id': self.review.id}),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
