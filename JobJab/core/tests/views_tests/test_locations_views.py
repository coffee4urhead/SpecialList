import json
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from JobJab.core.models import CustomUser, UserLocation, Notification
from JobJab.core.views.location import UpdateGeolocationView, UserLocationWithConnectionsView


class UpdateGeolocationViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = CustomUser.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        self.location = UserLocation.objects.create(
            user=self.user,
            latitude=40.7128,
            longitude=-74.0060
        )

    def test_get_existing_location(self):
        request = self.factory.get(reverse('update_geolocation', kwargs={'username': 'testuser'}))
        request.user = self.user
        response = UpdateGeolocationView.as_view()(request, username='testuser')
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertTrue(data['exists'])
        self.assertEqual(float(data['latitude']), 40.7128)
        self.assertEqual(float(data['longitude']), -74.0060)

    def test_get_non_existing_location(self):
        request = self.factory.get(reverse('update_geolocation', kwargs={'username': 'otheruser'}))
        request.user = self.other_user
        response = UpdateGeolocationView.as_view()(request, username='otheruser')
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertFalse(data['exists'])
        self.assertEqual(data['message'], 'Location not found')

    def test_get_location_unauthorized(self):
        request = self.factory.get(reverse('update_geolocation', kwargs={'username': 'testuser'}))
        request.user = self.other_user
        response = UpdateGeolocationView.as_view()(request, username='testuser')
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'You can only access your own location')

    def test_post_create_location(self):
        data = {'latitude': 34.0522, 'longitude': -118.2437}
        request = self.factory.post(
            reverse('update_geolocation', kwargs={'username': 'otheruser'}),
            data=json.dumps(data),
            content_type='application/json'
        )
        request.user = self.other_user
        response = UpdateGeolocationView.as_view()(request, username='otheruser')
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['action'], 'created')
        self.assertEqual(float(data['latitude']), 34.0522)
        self.assertEqual(float(data['longitude']), -118.2437)

        notification = Notification.objects.filter(user=self.other_user).first()
        self.assertIsNotNone(notification)
        self.assertEqual(notification.title, f"Successfully attached location to user otheruser")

    def test_post_update_location(self):
        data = {'latitude': 34.0522, 'longitude': -118.2437}
        request = self.factory.post(
            reverse('update_geolocation', kwargs={'username': 'testuser'}),
            data=json.dumps(data),
            content_type='application/json'
        )
        request.user = self.user
        response = UpdateGeolocationView.as_view()(request, username='testuser')
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['action'], 'updated')
        self.assertEqual(float(data['latitude']), 34.0522)
        self.assertEqual(float(data['longitude']), -118.2437)

    def test_post_invalid_coordinates(self):
        data = {'latitude': 'invalid', 'longitude': -118.2437}
        request = self.factory.post(
            reverse('update_geolocation', kwargs={'username': 'testuser'}),
            data=json.dumps(data),
            content_type='application/json'
        )
        request.user = self.user
        response = UpdateGeolocationView.as_view()(request, username='testuser')
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Invalid coordinates format')

    def test_post_invalid_json(self):
        request = self.factory.post(
            reverse('update_geolocation', kwargs={'username': 'testuser'}),
            data='invalid json',
            content_type='application/json'
        )
        request.user = self.user
        response = UpdateGeolocationView.as_view()(request, username='testuser')
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 400)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Invalid JSON data')


class UserLocationWithConnectionsViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = CustomUser.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.follower1 = CustomUser.objects.create_user(
            username='follower1',
            email='follower1@example.com',
            password='testpass123'
        )
        self.follower2 = CustomUser.objects.create_user(
            username='follower2',
            email='follower2@example.com',
            password='testpass123'
        )
        self.following1 = CustomUser.objects.create_user(
            username='following1',
            email='following1@example.com',
            password='testpass123'
        )

        self.follower1.following.add(self.user)
        self.follower2.following.add(self.user)
        self.user.following.add(self.following1)

        self.user_location = UserLocation.objects.create(
            user=self.user,
            latitude=40.7128,
            longitude=-74.0060
        )
        self.follower1_location = UserLocation.objects.create(
            user=self.follower1,
            latitude=34.0522,
            longitude=-118.2437
        )
        self.follower2_location = UserLocation.objects.create(
            user=self.follower2,
            latitude=51.5074,
            longitude=-0.1278
        )
        self.following1_location = UserLocation.objects.create(
            user=self.following1,
            latitude=48.8566,
            longitude=2.3522
        )

    def test_get_user_location_with_connections(self):
        request = self.factory.get(reverse('user_location_with_connections', kwargs={'username': 'testuser'}))
        request.user = AnonymousUser()
        response = UserLocationWithConnectionsView.as_view()(request, username='testuser')
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(data['status'], 'success')

        self.assertEqual(float(data['user_location']['latitude']), 40.7128)
        self.assertEqual(float(data['user_location']['longitude']), -74.0060)
        self.assertEqual(data['user_location']['username'], 'testuser')

        self.assertEqual(len(data['connections']['followers']), 2)
        follower_usernames = {f['username'] for f in data['connections']['followers']}
        self.assertEqual(follower_usernames, {'follower1', 'follower2'})

        self.assertEqual(len(data['connections']['following']), 1)
        self.assertEqual(data['connections']['following'][0]['username'], 'following1')

    def test_get_user_location_not_found(self):
        new_user = CustomUser.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='testpass123'
        )
        request = self.factory.get(reverse('user_location_with_connections', kwargs={'username': 'newuser'}))
        request.user = AnonymousUser()
        response = UserLocationWithConnectionsView.as_view()(request, username='newuser')
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'Location not found')
        self.assertTrue(data['requires_location'])

    def test_get_user_not_found(self):
        request = self.factory.get(reverse('user_location_with_connections', kwargs={'username': 'nonexistent'}))
        request.user = AnonymousUser()
        response = UserLocationWithConnectionsView.as_view()(request, username='nonexistent')
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(data['status'], 'error')
        self.assertEqual(data['message'], 'User not found')

    def test_post_update_location(self):
        data = {'latitude': 35.6895, 'longitude': 139.6917}
        request = self.factory.post(
            reverse('user_location_with_connections', kwargs={'username': 'testuser'}),
            data=json.dumps(data),
            content_type='application/json'
        )
        request.user = self.user
        response = UserLocationWithConnectionsView.as_view()(request, username='testuser')
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(float(data['user_location']['latitude']), 35.6895)
        self.assertEqual(float(data['user_location']['longitude']), 139.6917)

        updated_location = UserLocation.objects.get(user=self.user)
        self.assertEqual(float(updated_location.latitude), 35.6895)
        self.assertEqual(float(updated_location.longitude), 139.6917)

    def test_post_update_location_unauthorized(self):
        data = {'latitude': 35.6895, 'longitude': 139.6917}
        request = self.factory.post(
            reverse('user_location_with_connections', kwargs={'username': 'testuser'}),
            data=json.dumps(data),
            content_type='application/json'
        )
        request.user = self.follower1
        response = UserLocationWithConnectionsView.as_view()(request, username='testuser')
        data = json.loads(response.content)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(float(data['user_location']['latitude']), 40.7128)
