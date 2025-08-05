from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.auth import get_user_model
import json

from JobJab.core.models import UserLocation, CustomUser
from JobJab.reviews.models import UserReview
from JobJab.core.forms import ProfileEditForm, UserOrganizationFormSet

User = get_user_model()


class AccountViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='pass12345',
            email='testuser@example.com'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            password='pass12345',
            email='otheruser@example.com'
        )

    def test_get_account_view_owner(self):
        self.client.login(username='testuser', password='pass12345')
        url = reverse('account_view', kwargs={'username': self.user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        self.assertIn('organization_formset', response.context)
        self.assertEqual(response.context['viewed_account'], self.user)

    def test_get_account_view_not_owner(self):
        self.client.login(username='otheruser', password='pass12345')
        url = reverse('account_view', kwargs={'username': self.user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['form'])
        self.assertIsNone(response.context['organization_formset'])
        self.assertEqual(response.context['viewed_account'], self.user)

    def test_post_account_view_not_owner_redirects(self):
        self.client.login(username='otheruser', password='pass12345')
        url = reverse('account_view', kwargs={'username': self.user.username})
        response = self.client.post(url, data={}, follow=False)
        self.assertRedirects(response, reverse('account_view', kwargs={'username': 'otheruser'}))

    def test_post_account_view_invalid_forms(self):
        self.client.login(username='testuser', password='pass12345')
        url = reverse('account_view', kwargs={'username': self.user.username})

        form_data = {
            'first_name': '',
            'last_name': '',
        }
        formset_data = {
            'form-TOTAL_FORMS': '0',
            'form-INITIAL_FORMS': '0',
        }
        post_data = {**form_data, **formset_data}

        response = self.client.post(url, data=post_data)

        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('correct the errors' in str(m).lower() for m in messages))
        self.assertIsInstance(response.context['form'], ProfileEditForm)
        self.assertIsInstance(response.context['organization_formset'], UserOrganizationFormSet)


class FollowersFollowingViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='user1',
            password='pass123',
            email='user1@example.com'
        )
        self.follower = User.objects.create_user(
            username='follower',
            password='pass123',
            email='follower@example.com'
        )
        self.following = User.objects.create_user(
            username='following',
            password='pass123',
            email='following@example.com'
        )

        self.user.followers.add(self.follower)
        self.following.followers.add(self.user)

        UserLocation.objects.create(user=self.follower, latitude=12.34, longitude=56.78)
        UserLocation.objects.create(user=self.following, latitude=23.45, longitude=67.89)

    def test_get_followers_following_view_html(self):
        url = reverse('user_connections', kwargs={'username': self.user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('followers', response.context)
        self.assertIn('following', response.context)
        self.assertTemplateUsed(response, 'template-components/follow_modal_content.html')

    def test_get_followers_following_view_ajax(self):
        url = reverse('user_connections', kwargs={'username': self.user.username})
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertIn('followers', data)
        self.assertIn('following', data)

        follower_data = data['followers'][0]
        self.assertEqual(follower_data['username'], self.follower.username)
        self.assertIsInstance(follower_data['latitude'], float)
        self.assertIsInstance(follower_data['longitude'], float)


class UpdateFollowersViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='user1',
            password='pass123',
            email='user1@example.com'
        )
        self.follower = User.objects.create_user(
            username='follower',
            password='pass123',
            email='follower@example.com'
        )
        self.client.login(username='follower', password='pass123')

    def test_post_invalid_request_type(self):
        url = reverse('update_followers', kwargs={'username': self.user.username, 'followerId': self.follower.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'status': 'error', 'message': 'Invalid request'})

    def test_post_invalid_json(self):
        url = reverse('update_followers', kwargs={'username': self.user.username, 'followerId': self.follower.id})
        response = self.client.post(url, data='not-json', content_type='application/json',
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'status': 'error', 'message': 'Invalid JSON'})

    def test_post_user_does_not_exist(self):
        url = reverse('update_followers', kwargs={'username': 'nonexistent', 'followerId': self.follower.id})
        data = json.dumps({'action': 'follow'})
        response = self.client.post(url, data=data, content_type='application/json',
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'status': 'error', 'message': 'User does not exist'})

    def test_post_follow_action(self):
        url = reverse('update_followers', kwargs={'username': self.user.username, 'followerId': self.follower.id})
        data = json.dumps({'action': 'follow'})
        response = self.client.post(url, data=data, content_type='application/json',
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'success', 'message': 'Now following'})

        self.assertIn(self.follower, self.user.followers.all())
        self.assertIn(self.user, self.follower.following.all())

    def test_post_unfollow_action(self):
        self.user.followers.add(self.follower)
        self.follower.following.add(self.user)

        url = reverse('update_followers', kwargs={'username': self.user.username, 'followerId': self.follower.id})
        data = json.dumps({'action': 'unfollow'})
        response = self.client.post(url, data=data, content_type='application/json',
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'status': 'success', 'message': 'Unfollowed'})

        self.assertNotIn(self.follower, self.user.followers.all())
        self.assertNotIn(self.user, self.follower.following.all())

    def test_post_invalid_action(self):
        url = reverse('update_followers', kwargs={'username': self.user.username, 'followerId': self.follower.id})
        data = json.dumps({'action': 'invalid'})
        response = self.client.post(url, data=data, content_type='application/json',
                                    HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(response.content, {'status': 'error', 'message': 'Invalid action'})
