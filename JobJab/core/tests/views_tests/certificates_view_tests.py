from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from unittest.mock import patch
from JobJab.core.models import CustomUser, Certificate, Notification

class CertificatesViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = CustomUser.objects.create_user(
            username='user1',
            password='pass123',
            email='user1@example.com'
        )
        self.other_user = CustomUser.objects.create_user(
            username='otheruser',
            password='pass123',
            email='otheruser@example.com'
        )
        self.client.login(username='user1', password='pass123')

        with patch('JobJab.core.models.Certificate.generate_preview'):
            self.certificate = Certificate.objects.create(
                user=self.user,
                title='Valid Certificate Title',
                certificate_file=SimpleUploadedFile(
                    "file.pdf", b"file_content", content_type="application/pdf"
                )
            )

    def test_user_certificates_get(self):
        url = reverse('user_certificates', kwargs={'username': self.user.username})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('certificates', response.context)
        self.assertIn(self.certificate, response.context['certificates'])

    @patch('JobJab.core.models.Certificate.generate_preview')
    def test_user_certificates_post_valid(self, mock_generate):
        url = reverse('user_certificates', kwargs={'username': self.user.username})
        file = SimpleUploadedFile("newcert.pdf", b"file_content", content_type="application/pdf")
        data = {
            'title': 'New Valid Certificate',
            'certificate_file': file,
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            Certificate.objects.filter(title='New Valid Certificate', user=self.user).exists()
        )
        self.assertTrue(
            Notification.objects.filter(
                user=self.user, title__icontains='Successful Certificate Upload'
            ).exists()
        )
        mock_generate.assert_called_once()

    @patch('JobJab.core.models.Certificate.generate_preview')
    def test_edit_certificate_get(self, mock_generate):
        url = reverse('edit_certificate', kwargs={'certificate_id': self.certificate.id})
        response = self.client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertIn('form_html', response.json())
        mock_generate.assert_not_called()

    @patch('JobJab.core.models.Certificate.generate_preview')
    def test_edit_certificate_post_valid(self, mock_generate):
        url = reverse('edit_certificate', kwargs={'certificate_id': self.certificate.id})
        data = {
            'title': 'Updated Cert Title',
        }
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.certificate.refresh_from_db()
        self.assertEqual(self.certificate.title, 'Updated Cert Title')
        self.assertTrue(
            Notification.objects.filter(user=self.user, title__icontains='Successful Certificate Edit').exists()
        )
        mock_generate.assert_called_once()

    @patch('JobJab.core.models.Certificate.generate_preview')
    def test_edit_certificate_post_invalid(self, mock_generate):
        url = reverse('edit_certificate', kwargs={'certificate_id': self.certificate.id})
        data = {
            'title': '',
        }
        response = self.client.post(url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        mock_generate.assert_called_once()

    @patch('JobJab.core.models.Certificate.generate_preview')
    def test_delete_certificate_post_owner(self, mock_generate):
        url = reverse('delete_certificate', kwargs={'cert_id': self.certificate.id})
        response = self.client.post(url)
        self.assertRedirects(response, reverse('user_certificates', kwargs={'username': self.user.username}))
        self.assertFalse(Certificate.objects.filter(id=self.certificate.id).exists())
        self.assertTrue(
            Notification.objects.filter(user=self.user, title__icontains='Successfully deleted certificate').exists()
        )
        mock_generate.assert_not_called()

    @patch('JobJab.core.models.Certificate.generate_preview')
    def test_delete_certificate_post_not_owner(self, mock_generate):
        self.client.logout()
        self.client.login(username='otheruser', password='pass123')
        url = reverse('delete_certificate', kwargs={'cert_id': self.certificate.id})
        response = self.client.post(url)
        self.assertRedirects(response, reverse('user_certificates', kwargs={'username': 'otheruser'}))
        self.assertTrue(Certificate.objects.filter(id=self.certificate.id).exists())
        mock_generate.assert_not_called()