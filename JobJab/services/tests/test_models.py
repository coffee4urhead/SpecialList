from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date, time

from JobJab.services.models import (
    Availability, AvailabilityType, Comment, ServiceListing,
    DeletedService, ServiceDetailSection, CategoryChoices
)

User = get_user_model()

class AvailabilityModelTests(TestCase):
    def setUp(self):
        self.provider = User.objects.create_user(username='provider1', password='pass', user_type='provider', email='provider@gmail.com')

    def test_create_availability_and_str(self):
        avail = Availability.objects.create(
            provider=self.provider,
            date=date.today(),
            start_time=time(9, 0),
            end_time=time(17, 0),
            status=AvailabilityType.AVAILABLE,
            note="Test availability"
        )
        self.assertEqual(avail.status, AvailabilityType.AVAILABLE)
        self.assertIn("provider1", str(avail))


class CommentModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user1', password='pass', email='provider@gmail.com')

    def test_comment_creation_and_str(self):
        comment = Comment.objects.create(content="Test comment", author=self.user)
        self.assertFalse(comment.is_reply)
        self.assertIn("user1", str(comment))

    def test_reply_comment(self):
        parent_comment = Comment.objects.create(content="Parent", author=self.user)
        reply_comment = Comment.objects.create(content="Reply", author=self.user, parent=parent_comment)
        self.assertTrue(reply_comment.is_reply)
        self.assertEqual(reply_comment.parent, parent_comment)


class ServiceListingModelTests(TestCase):
    def setUp(self):
        self.provider = User.objects.create_user(username='provider1', password='pass', email='provider@gmail.com')

    def test_service_creation_and_str(self):
        service = ServiceListing.objects.create(
            provider=self.provider,
            title="Test Service",
            description="A test service",
            location="Bulgaria/Sofia City",
            category=CategoryChoices.Other,
            price=99.99,
            duration_minutes=45,
        )
        self.assertEqual(str(service), "Test Service by provider1")
        self.assertTrue(service.is_active)

    def test_deactivate_service(self):
        service = ServiceListing.objects.create(
            provider=self.provider,
            title="Service to deactivate",
            location="Bulgaria/Sofia City",
            category=CategoryChoices.Other,
            price=50.00,
            duration_minutes=30,
        )
        service.deactivate_service(user=self.provider, reason="No longer offered", is_deleted=True)
        self.assertFalse(service.is_active)
        self.assertTrue(service.is_deleted)
        self.assertEqual(service.deactivated_by, self.provider)
        self.assertEqual(service.deactivation_reason, "No longer offered")
        self.assertIsNotNone(service.deactivated_at)


class DeletedServiceModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='deleter', password='pass', email='provider@gmail.com')

    def test_deleted_service_creation_and_ordering(self):
        data = {'title': 'Deleted Service', 'price': 123.45}
        ds = DeletedService.objects.create(service_data=data, deleted_by=self.user)
        self.assertEqual(ds.deleted_by, self.user)
        self.assertEqual(ds.service_data['title'], 'Deleted Service')


class ServiceDetailSectionModelTests(TestCase):
    def setUp(self):
        self.provider = User.objects.create_user(username='provider1', password='pass', email='provider@gmail.com')
        self.service = ServiceListing.objects.create(
            provider=self.provider,
            title="Service with Sections",
            location="Bulgaria/Sofia City",
            category=CategoryChoices.Other,
            price=20.00,
            duration_minutes=60,
        )

    def test_create_text_image_section_and_str(self):
        section = ServiceDetailSection.objects.create(
            service=self.service,
            section_type='text_image',
            order=1,
            title="Intro",
            content="Welcome to this service",
        )
        self.assertEqual(section.get_list_items(), [])
        self.assertIn("Text with Image", str(section))

    def test_create_list_section_with_list_items(self):
        section = ServiceDetailSection.objects.create(
            service=self.service,
            section_type='list',
            order=2,
            list_items=['Item 1', 'Item 2', 'Item 3']
        )
        self.assertEqual(section.get_list_items(), ['Item 1', 'Item 2', 'Item 3'])
