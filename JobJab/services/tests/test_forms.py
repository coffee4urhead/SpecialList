from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date, time

from JobJab.services.forms import (
    AvailabilityForm, ServiceListingForm, ServiceDetailSectionForm, CommentForm
)
from JobJab.services.models import CategoryChoices, ServiceDetailSection

class AvailabilityFormTests(TestCase):
    def test_valid_data(self):
        form = AvailabilityForm(data={
            'date': date.today(),
            'start_time': time(9, 0),
            'end_time': time(17, 0),
            'status': 'available',
            'note': 'Available on weekdays',
        })
        self.assertTrue(form.is_valid())

    def test_missing_required_field(self):
        form = AvailabilityForm(data={
            'date': '',
            'start_time': time(9, 0),
            'end_time': time(17, 0),
            'status': 'available',
        })
        self.assertFalse(form.is_valid())
        self.assertIn('date', form.errors)


class ServiceListingFormTests(TestCase):
    def test_valid_data(self):
        form = ServiceListingForm(data={
            'title': 'Test Service',
            'description': 'Test description',
            'location': 'Bulgaria/Sofia City',
            'category': CategoryChoices.Other,
            'price': 50.00,
            'duration_minutes': 30,
            'is_active': True,
        })
        self.assertTrue(form.is_valid())

    def test_missing_required_field(self):
        form = ServiceListingForm(data={
            'description': 'Test description',
            'location': 'Bulgaria/Sofia City',
            'category': CategoryChoices.Other,
            'price': 50.00,
            'duration_minutes': 30,
            'is_active': True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)


class ServiceDetailSectionFormTests(TestCase):
    def test_default_section_type(self):
        form = ServiceDetailSectionForm()
        self.assertEqual(form.initial['section_type'], 'text_image')

    def test_list_section_valid_with_textarea_list(self):
        data = {
            'section_type': 'list',
            'list_items': "Item 1\nItem 2\nItem 3",
        }
        form = ServiceDetailSectionForm(data=data)
        self.assertTrue(form.is_valid())

        cleaned = form.clean()
        self.assertEqual(cleaned['list_items'], '["Item 1", "Item 2", "Item 3"]')

    def test_list_section_valid_with_json_list(self):
        data = {
            'section_type': 'list',
            'list_items': '["One", "Two", "Three"]',
        }
        form = ServiceDetailSectionForm(data=data)
        self.assertTrue(form.is_valid())

    def test_list_section_invalid_json(self):
        data = {
            'section_type': 'list',
            'list_items': '[invalid json]',
        }
        form = ServiceDetailSectionForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('list_items', form.errors)

    def test_list_section_missing_list_items(self):
        form = ServiceDetailSectionForm(data={'section_type': 'list', 'list_items': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('list_items', form.errors)

    def test_text_image_section_requires_content_and_image(self):
        form = ServiceDetailSectionForm(data={'section_type': 'text_image'})
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)
        self.assertIn('image', form.errors)

    def test_text_image_section_with_content_only(self):
        form = ServiceDetailSectionForm(data={'section_type': 'text_image', 'content': 'Some content'})
        self.assertFalse(form.is_valid())
        self.assertIn('image', form.errors)

    def test_text_image_section_with_image_only(self):
        image_file = SimpleUploadedFile("test_image.jpg", b"file_content", content_type="image/jpeg")
        form = ServiceDetailSectionForm(data={'section_type': 'text_image', 'content': ''}, files={'image': image_file})
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)

class CommentFormTests(TestCase):
    def test_valid_content(self):
        form = CommentForm(data={'content': 'This is a test comment'})
        self.assertTrue(form.is_valid())

    def test_empty_content(self):
        form = CommentForm(data={'content': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('content', form.errors)
