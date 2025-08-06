from urllib.parse import urlencode

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages

from JobJab import settings
from JobJab.core.models import Notification
from JobJab.reviews.models import WebsiteReview
from JobJab.reviews.forms import WebsiteReviewForm

User = get_user_model()


class CoreViewsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='StrongPass123!'
        )

        for i in range(5):
            WebsiteReview.objects.create(
                reviewer=self.user,
                rating=4,
                comment=f'Test review {i}'
            )
        for i in range(3):
            Notification.objects.create(
                user=self.user,
                message=f'Notification {i}',
                is_read=False
            )

    def test_home_view_anonymous(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('reviews_from_user_to_the_website', response.context)
        self.assertEqual(response.context['unread_count'], 0)
        self.assertTemplateUsed(response, 'core/home.html')

    def test_home_view_authenticated(self):
        self.client.login(username='testuser', password='StrongPass123!')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['unread_count'], 3)
        self.assertEqual(len(response.context['reviews_from_user_to_the_website']), 4)

    def test_about_view_get_anonymous(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['website_review_form'], WebsiteReviewForm)
        self.assertFalse(response.context['website_review_form'].fields.get('reviewer', False))
        self.assertEqual(response.context['unread_count'], 0)

    def test_about_view_get_authenticated(self):
        self.client.login(username='testuser', password='StrongPass123!')
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context['website_review_form'], WebsiteReviewForm)
        self.assertEqual(response.context['unread_count'], 3)

    def test_about_view_post_anonymous_redirects_to_login(self):
        response = self.client.post(reverse('about'), data={'rating': 5, 'comment': 'Great site!'})

        login_url = reverse('login')
        about_url = reverse('about')

        expected_redirect = f'{login_url}'

        self.assertRedirects(response, expected_redirect)

    def test_about_view_post_authenticated_valid(self):
        login_successful = self.client.login(username='testuser', password='StrongPass123!')
        self.assertTrue(login_successful, "Login failed for testuser")

        form_data = {
            'rating': 5,
            'main_caption': 'Great Site',
            'comment': 'Excellent website!'
        }
        response = self.client.post(reverse('about'), data=form_data, follow=True)
        self.assertEqual(response.status_code, 200)

        self.assertTrue(WebsiteReview.objects.filter(comment='Excellent website!').exists())

    def test_about_view_post_authenticated_invalid(self):
        self.client.login(username='testuser', password='StrongPass123!')
        form_data = {
            'comment': 'No rating provided'
        }
        response = self.client.post(reverse('about'), data=form_data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['website_review_form'].is_valid())

    def test_privacy_policy_view(self):
        response = self.client.get(reverse('privacy_policy'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'template-components/description-component.html')

    def test_notification_view_existing_user(self):
        self.client.login(username='testuser', password='StrongPass123!')
        response = self.client.get(reverse('notifications', kwargs={'username': self.user.username}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['account'], self.user)
        self.assertEqual(response.context['unread_count'], 0)
        self.assertEqual(response.context['total_count'], 3)
        self.assertTemplateUsed(response, 'core/notification-page.html')

    def test_notification_view_nonexistent_user(self):
        response = self.client.get(reverse('notifications', kwargs={'username': 'nonexistentuser'}))
        self.assertEqual(response.status_code, 404)
