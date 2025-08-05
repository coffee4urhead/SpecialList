from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import time
import os

from ..models import (
    Organization, UserOrganization, Certificate,
    CustomUser, UserLocation, Notification,
    BlacklistItem, UserBlacklistProfile
)
from ...services.models import ServiceListing

User = get_user_model()

class OrganizationModelTest(TestCase):
    def setUp(self):
        self.org = Organization.objects.create(
            name="Test Org",
            website="https://test.org"
        )

    def test_organization_creation(self):
        self.assertEqual(self.org.name, "Test Org")
        self.assertEqual(self.org.website, "https://test.org")
        self.assertTrue(self.org.logo.name.endswith('default-org.jpg'))

    def test_organization_str(self):
        self.assertEqual(str(self.org), "Test Org")


class UserOrganizationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpasss123"
        )
        self.org = Organization.objects.create(name="Test Org")
        self.user_org = UserOrganization.objects.create(
            user=self.user,
            organization=self.org,
            position="Developer",
            is_current=True
        )

    def test_user_organization_creation(self):
        self.assertEqual(self.user_org.user.username, "testuser")
        self.assertEqual(self.user_org.organization.name, "Test Org")
        self.assertEqual(self.user_org.position, "Developer")
        self.assertTrue(self.user_org.is_current)

    def test_unique_together_constraint(self):
        with self.assertRaises(Exception):
            UserOrganization.objects.create(
                user=self.user,
                organization=self.org,
                position="Duplicate"
            )


class CertificateModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="certuser",
            email="cert@example.com",
            password="testpasss123"
        )
        self.cert = Certificate.objects.create(
            user=self.user,
            title="Python Developer Certification",
            is_verified=True
        )

    def test_certificate_creation(self):
        self.assertEqual(self.cert.title, "Python Developer Certification")
        self.assertTrue(self.cert.is_verified)
        self.assertIsNotNone(self.cert.uploaded_at)

    def test_certificate_str(self):
        self.assertEqual(
            str(self.cert),
            "certuser - Python Developer Certification"
        )

    def test_generate_preview(self):
        # This would need a mock PDF file in a real test
        pass


class CustomUserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpasss123",
            user_type="freelancer"
        )

    def test_user_creation(self):
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.email, "test@example.com")
        self.assertEqual(self.user.user_type, "freelancer")
        self.assertFalse(self.user.is_verified)

    def test_user_str(self):
        self.assertEqual(str(self.user), "testuser -  ")

    def test_followers_following(self):
        user2 = User.objects.create_user(
            username="user2",
            email="user2@example.com",
            password="testpasss123"
        )
        user2.following.add(self.user)
        self.user.followers.add(user2)

        self.assertEqual(self.user.get_user_followers(), 1)
        self.assertEqual(user2.get_user_following(), 1)


class UserLocationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="locationuser",
            email="location@example.com",
            password="testpasss123"
        )
        self.location = UserLocation.objects.create(
            user=self.user,
            latitude=40.7128,
            longitude=-74.0060
        )

    def test_location_creation(self):
        self.assertEqual(self.location.user.username, "locationuser")
        self.assertEqual(float(self.location.latitude), 40.7128)
        self.assertEqual(float(self.location.longitude), -74.0060)
        self.assertIsNotNone(self.location.last_updated)

    def test_location_str(self):
        self.assertEqual(
            str(self.location),
            "locationuser's location"
        )


class NotificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="notifyuser",
            email="notify@example.com",
            password="testpasss123"
        )
        self.notification = Notification.objects.create(
            user=self.user,
            title="Test Notification",
            message="This is a test message",
            notification_type="info"
        )

    def test_notification_creation(self):
        self.assertEqual(self.notification.title, "Test Notification")
        self.assertEqual(self.notification.message, "This is a test message")
        self.assertEqual(self.notification.notification_type, "info")
        self.assertFalse(self.notification.is_read)

    def test_mark_as_read(self):
        self.notification.mark_as_read()
        self.assertTrue(self.notification.is_read)

    def test_create_notification_classmethod(self):
        notification = Notification.create_notification(
            user=self.user,
            title="Classmethod Test",
            message="Created via classmethod"
        )
        self.assertEqual(notification.title, "Classmethod Test")


class BlacklistItemModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="blacklistuser",
            email="blacklist@example.com",
            password="testpasss123"
        )
        self.reporter = User.objects.create_user(
            username="reporter",
            email="reporter@example.com",
            password="testpasss123"
        )
        self.service = ServiceListing.objects.create(
            provider=self.user,
            title="Test Service",
            price=123,
            description="Test Description"
        )
        content_type = ContentType.objects.get_for_model(self.service)
        self.blacklist_item = BlacklistItem.objects.create(
            reporter=self.reporter,
            content_type=content_type,
            object_id=self.service.id,
            reason="spam",
            description="This is spam"
        )

    def test_blacklist_item_creation(self):
        self.assertEqual(self.blacklist_item.reporter.username, "reporter")
        self.assertEqual(self.blacklist_item.reason, "spam")
        self.assertEqual(self.blacklist_item.status, "pending")

    def test_clean_method(self):
        # Test self-reporting validation
        with self.assertRaises(ValidationError):
            bad_item = BlacklistItem(
                reporter=self.user,
                content_type=ContentType.objects.get_for_model(self.service),
                object_id=self.service.id,
                reason="spam"
            )
            bad_item.clean()

    def test_approve_report(self):
        moderator = User.objects.create_user(
            username="moderator",
            email="mod@example.com",
            password="testpasss123"
        )
        self.blacklist_item.approve_report(moderator, "Test notes")
        self.assertEqual(self.blacklist_item.status, "approved")
        self.assertEqual(self.blacklist_item.moderator, moderator)
        self.service.refresh_from_db()
        self.assertFalse(self.service.is_active)


class UserBlacklistProfileModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="banneduser",
            email="banned@example.com",
            password="testpasss123"
        )
        self.moderator = User.objects.create_user(
            username="moderator",
            email="mod@example.com",
            password="testpasss123"
        )
        self.profile = UserBlacklistProfile.objects.create(
            user=self.user,
            is_banned=True,
            ban_reason="Test ban",
            banned_by=self.moderator
        )

    def test_profile_creation(self):
        self.assertEqual(self.profile.user.username, "banneduser")
        self.assertTrue(self.profile.is_banned)
        self.assertEqual(self.profile.ban_reason, "Test ban")

    def test_ban_user(self):
        self.profile.ban_user(self.moderator, "Serious violation")
        self.assertTrue(self.profile.is_banned)
        self.assertFalse(self.user.is_active)

    def test_unban_user(self):
        self.profile.unban_user(self.moderator, "Appeal approved")
        self.assertFalse(self.profile.is_banned)
        self.assertTrue(self.user.is_active)