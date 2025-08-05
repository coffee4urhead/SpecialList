from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from JobJab.core.models import Notification, NotificationType

User = get_user_model()


class AuthViewTests(TestCase):
    def test_register_get(self):
        url = reverse('register')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_register_post_valid(self):
        url = reverse('register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'strongpassword123',
            'password2': 'strongpassword123',
        }
        response = self.client.post(url, data)
        self.assertRedirects(response, reverse('login'))

        user_exists = User.objects.filter(username='newuser').exists()
        self.assertTrue(user_exists)

        user = User.objects.get(username='newuser')
        notification = Notification.objects.filter(user=user, notification_type=NotificationType.INFO).first()
        self.assertIsNotNone(notification)
        self.assertIn("Welcome to JobJab", notification.title)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Account created for newuser' in str(m) for m in messages))

    def test_register_post_invalid(self):
        url = reverse('register')
        data = {
            'username': 'newuser',
            'user_type': 'newuser',
            'email': 'not-an-email',
            'password1': '123',
            'password2': '456',
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertTrue(response.context['form'].errors)

    def test_login_get(self):
        url = reverse('login')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    def test_login_post_valid(self):
        user = User.objects.create_user(username='loginuser', password='testpassword')

        url = reverse('login')
        data = {
            'username': 'loginuser',
            'password': 'testpassword',
        }
        response = self.client.post(url, data)

        self.assertRedirects(response, reverse('home'))

        user_id = self.client.session.get('_auth_user_id')
        self.assertEqual(int(user_id), user.pk)

    def test_login_post_valid_staff(self):
        user = User.objects.create_user(username='staffuser', password='staffpass', is_staff=True)

        url = reverse('login')
        data = {
            'username': 'staffuser',
            'password': 'staffpass',
        }
        response = self.client.post(url, data)

        self.assertRedirects(response, reverse('custom_admin_home'))

        user_id = self.client.session.get('_auth_user_id')
        self.assertEqual(int(user_id), user.pk)

    def test_login_post_invalid(self):
        url = reverse('login')
        data = {
            'username': 'nosuchuser',
            'password': 'wrongpassword',
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Invalid username or password' in str(m) for m in messages))

    def test_logout_get(self):
        user = User.objects.create_user(username='logoutuser', password='testpass')
        self.client.login(username='logoutuser', password='testpass')

        url = reverse('logout')
        response = self.client.get(url)
        self.assertRedirects(response, reverse('home'))

        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('logged out successfully' in str(m).lower() for m in messages))

        self.assertNotIn('_auth_user_id', self.client.session)
