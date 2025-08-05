from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.utils.timezone import now, timedelta

from JobJab.core.forms import (
    CleanUserCreationForm,
    CleanLoginForm,
    ProfileEditForm,
    CertificateForm,
    BlacklistItemForm,
)
from JobJab.core.models import CustomUser, UserOrganization, Certificate, BlacklistItem
from django.contrib.auth import authenticate

User = get_user_model()


class CleanUserCreationFormTests(TestCase):
    def test_valid_user_creation(self):
        form_data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'user_type': 'seeker',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        }
        form = CleanUserCreationForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_password_too_short(self):
        form_data = {
            'username': 'shortpass',
            'email': 'short@example.com',
            'user_type': 'client',
            'password1': 'Short1!',
            'password2': 'Short1!',
        }
        form = CleanUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Password must be at least 10 characters long.', form.errors['password2'])

    def test_password_missing_uppercase(self):
        form_data = {
            'username': 'noupcase',
            'email': 'no@upper.com',
            'user_type': 'client',
            'password1': 'lowercase123!',
            'password2': 'lowercase123!',
        }
        form = CleanUserCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('Password must contain at least one uppercase letter.', form.errors['password2'])


class CleanLoginFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='loginuser',
            password='ValidPass123!',
            email='login@example.com'
        )

    def test_login_valid(self):
        form = CleanLoginForm(data={'username': 'loginuser', 'password': 'ValidPass123!'})
        self.assertTrue(form.is_valid())

    def test_login_invalid(self):
        form = CleanLoginForm(data={'username': 'loginuser', 'password': 'WrongPass!'})
        self.assertFalse(form.is_valid())
        self.assertIn('Invalid username or password.', form.errors['__all__'])


class ProfileEditFormTests(TestCase):
    def test_profile_edit_form_valid(self):
        user = User.objects.create_user(username='edituser', email='edit@example.com', password='pass12345')
        form_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'edit@example.com',
            'bio': 'A nice person.',
            'phone_number': '1234567890',
            'timezone': 'UTC',
            'user_type': 'seeker'
        }
        form = ProfileEditForm(data=form_data, instance=user)
        self.assertTrue(form.is_valid())


class CertificateFormTests(TestCase):
    def test_certificate_title_too_short(self):
        cert_file = SimpleUploadedFile("file.pdf", b"Dummy content", content_type="application/pdf")
        form_data = {'title': 'Short'}
        form = CertificateForm(data=form_data, files={'certificate_file': cert_file})
        self.assertFalse(form.is_valid())
        self.assertIn('Certificate title must be at least 10 characters long', form.errors['title'])

    def test_valid_certificate_form(self):
        cert_file = SimpleUploadedFile("file.pdf", b"Dummy content", content_type="application/pdf")
        form_data = {'title': 'Valid Certificate Title'}
        form = CertificateForm(data=form_data, files={'certificate_file': cert_file})
        self.assertTrue(form.is_valid())


class BlacklistItemFormTests(TestCase):
    def setUp(self):
        self.reporter = User.objects.create_user(username='reporter', password='passs12345',
                                                 email='reporter@example.com')
        self.offender = User.objects.create_user(username='offender', password='passs12345',
                                                 email='offender@example.com')

    def test_blacklist_form_valid(self):
        form_data = {
            'reason': 'spam',
            'description': 'This user posted inappropriate content.',
        }
        form = BlacklistItemForm(
            data=form_data,
            reported_object=self.offender,
            reporter=self.reporter
        )
        self.assertTrue(form.is_valid())

        item = form.save()  # No need for commit=False now
        self.assertEqual(item.reporter, self.reporter)
        self.assertEqual(item.content_object, self.offender)

    def test_blacklist_reporting_self_invalid(self):
        form_data = {
            'reason': 'spam',
            'description': 'I am reporting myself',
        }
        form = BlacklistItemForm(
            data=form_data,
            reporter=self.reporter,
            reported_object=self.reporter
        )
        self.assertFalse(form.is_valid())
        self.assertIn('You cannot report your own content.', form.non_field_errors())

    def test_blacklist_description_too_short(self):
        form_data = {
            'reason': 'harassment',
            'description': 'Too short',
        }
        form = BlacklistItemForm(
            data=form_data,
            reporter=self.reporter,
            reported_object=self.offender
        )
        self.assertFalse(form.is_valid())
        self.assertIn(
            'Please provide more details (at least 10 characters) about your report.',
            form.non_field_errors()
        )
