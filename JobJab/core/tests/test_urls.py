from django.test import SimpleTestCase
from django.urls import reverse, resolve
from django.contrib.auth import views as auth_views

from JobJab.core.views import (
    auth, location, certificates, account, payments
)
from JobJab.core import main_views


class TestCoreUrls(SimpleTestCase):

    def test_home_url_resolves(self):
        url = reverse('home')
        self.assertEqual(resolve(url).func.view_class, main_views.HomeView)

    def test_about_url_resolves(self):
        url = reverse('about')
        self.assertEqual(resolve(url).func.view_class, main_views.AboutView)

    def test_privacy_policy_url_resolves(self):
        url = reverse('privacy_policy')
        self.assertEqual(resolve(url).func.view_class, main_views.PrivacyPolicyView)

    def test_register_url_resolves(self):
        url = reverse('register')
        self.assertEqual(resolve(url).func.view_class, auth.RegisterView)

    def test_login_url_resolves(self):
        url = reverse('login')
        self.assertEqual(resolve(url).func.view_class, auth.LoginView)

    def test_logout_url_resolves(self):
        url = reverse('logout')
        self.assertEqual(resolve(url).func.view_class, auth.LogoutView)

    def test_password_reset_urls(self):
        self.assertEqual(resolve(reverse('password_reset')).func.view_class, auth_views.PasswordResetView)
        self.assertEqual(resolve(reverse('password_reset_done')).func.view_class, auth_views.PasswordResetDoneView)
        self.assertEqual(resolve(reverse('password_reset_complete')).func.view_class, auth_views.PasswordResetCompleteView)

    def test_password_reset_confirm_url(self):
        url = reverse('password_reset_confirm', kwargs={'uidb64': 'uid', 'token': 'token'})
        self.assertEqual(resolve(url).func.view_class, auth_views.PasswordResetConfirmView)

    def test_user_account_view(self):
        url = reverse('account_view', kwargs={'username': 'john'})
        self.assertEqual(resolve(url).func.view_class, account.AccountView)

    def test_user_connections_view(self):
        url = reverse('user_connections', kwargs={'username': 'john'})
        self.assertEqual(resolve(url).func.view_class, account.FollowersFollowingView)

    def test_update_followers_view(self):
        url = reverse('update_followers', kwargs={'username': 'john', 'followerId': 1})
        self.assertEqual(resolve(url).func.view_class, account.UpdateFollowersView)

    def test_user_location_with_connections_view(self):
        url = reverse('user_location_with_connections', kwargs={'username': 'john'})
        self.assertEqual(resolve(url).func.view_class, location.UserLocationWithConnectionsView)

    def test_user_certificates_view(self):
        url = reverse('user_certificates', kwargs={'username': 'john'})
        self.assertEqual(resolve(url).func.view_class, certificates.UserCertificatesView)

    def test_user_payments_view(self):
        url = reverse('user_payments', kwargs={'username': 'john'})
        self.assertEqual(resolve(url).func.view_class, payments.UserPaymentsView)

    def test_notifications_view(self):
        url = reverse('notifications', kwargs={'username': 'john'})
        self.assertEqual(resolve(url).func.view_class, main_views.NotificationView)

    def test_update_geolocation_view(self):
        url = reverse('update_geolocation', kwargs={'username': 'john'})
        self.assertEqual(resolve(url).func.view_class, location.UpdateGeolocationView)

    def test_delete_certificate_view(self):
        url = reverse('delete_certificate', kwargs={'cert_id': 42})
        self.assertEqual(resolve(url).func.view_class, certificates.DeleteCertificateView)

    def test_edit_certificate_view(self):
        url = reverse('edit_certificate', kwargs={'certificate_id': 99})
        self.assertEqual(resolve(url).func.view_class, certificates.EditCertificateView)
