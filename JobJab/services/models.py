import json

from django.core.validators import MinLengthValidator
from django.db import models
from django.conf import settings

from JobJab.core.models import UserChoices
from JobJab.settings import AUTH_USER_MODEL


class AvailabilityType(models.TextChoices):
    AVAILABLE = 'available', 'Available'
    UNAVAILABLE = 'unavailable', 'Unavailable'


class Availability(models.Model):
    provider = models.ForeignKey(
        AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': UserChoices.Provider},
        related_name='availabilities'
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=12,
        choices=AvailabilityType,
        default=AvailabilityType.AVAILABLE
    )
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['date', 'start_time']

    def __str__(self):
        return f"{self.provider} - {self.status} on {self.date} from {self.start_time} to {self.end_time}"


class CategoryChoices(models.TextChoices):
    # Professional Services
    LEGAL = 'Legal', 'Legal Services'
    ACCOUNTING = 'Accounting', 'Accounting & Finance'
    CONSULTING = 'Consulting', 'Business Consulting'
    HUMAN_RESOURCES = 'HR', 'Human Resources'
    MARKETING = 'Marketing', 'Marketing & Advertising'

    # Healthcare & Wellness
    HEALTHCARE = 'Healthcare', 'Healthcare Services'
    FITNESS = 'Fitness', 'Fitness & Training'
    MENTAL_HEALTH = 'MentalHealth', 'Mental Health'
    NUTRITION = 'Nutrition', 'Nutrition & Diet'
    BEAUTY = 'Beauty', 'Beauty & Cosmetics'

    # Creative & Technical
    DESIGN = 'Design', 'Graphic & Design'
    DEVELOPMENT = 'Development', 'Web & App Development'
    WRITING = 'Writing', 'Writing & Editing'
    PHOTOGRAPHY = 'Photography', 'Photography'
    VIDEO = 'Video', 'Video & Animation'
    MUSIC = 'Music', 'Music & Audio'

    # Trade & Home Services
    CONSTRUCTION = 'Construction', 'Construction & Remodeling'
    ELECTRICAL = 'Electrical', 'Electrical Services'
    PLUMBING = 'Plumbing', 'Plumbing'
    CLEANING = 'Cleaning', 'Cleaning Services'
    LANDSCAPING = 'Landscaping', 'Landscaping & Gardening'

    # Education & Training
    TUTORING = 'Tutoring', 'Tutoring & Lessons'
    LANGUAGE = 'Language', 'Language Teaching'
    MUSIC_LESSONS = 'MusicLessons', 'Music Lessons'
    TEST_PREP = 'TestPrep', 'Test Preparation'
    WORKSHOPS = 'Workshops', 'Workshops & Classes'

    # Technology
    IT_SUPPORT = 'IT', 'IT Support'
    CYBERSECURITY = 'Cybersecurity', 'Cybersecurity'
    DATA_ANALYTICS = 'Data', 'Data Analytics'
    AI = 'AI', 'Artificial Intelligence'
    BLOCKCHAIN = 'Blockchain', 'Blockchain Services'

    # Events & Hospitality
    EVENT_PLANNING = 'Events', 'Event Planning'
    CATERING = 'Catering', 'Catering Services'
    PHOTOBOOTH = 'Photobooth', 'Photobooth Rental'
    DJ = 'DJ', 'DJ Services'

    # Transportation
    DELIVERY = 'Delivery', 'Delivery Services'
    TRANSPORT = 'Transport', 'Transportation'
    LOGISTICS = 'Logistics', 'Logistics Services'

    # Other Services
    PET = 'Pet', 'Pet Services'
    SENIOR = 'Senior', 'Senior Care'
    CHILDCARE = 'Childcare', 'Childcare'
    PERSONAL_ASSISTANT = 'PA', 'Personal Assistant'
    VIRTUAL_ASSISTANT = 'VA', 'Virtual Assistant'
    Other = 'Other', 'Other'


class Comment(models.Model):
    content = models.TextField()
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey('self', null=True, blank=True,
                               on_delete=models.CASCADE,
                               related_name='children')

    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author}: {self.content[:50]}"

    @property
    def is_reply(self):
        return self.parent is not None

class ServiceListing(models.Model):
    provider = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='services')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    service_photo = models.ImageField(upload_to='services/photos', blank=True)
    location = models.CharField(max_length=100, default='Bulgaria/Sofia', help_text='Specify location in the format Country/(city, province, village etc.)', validators=[MinLengthValidator(10)])
    category = models.CharField(choices=CategoryChoices, default=CategoryChoices.Other)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.PositiveIntegerField(default=60)
    is_active = models.BooleanField(default=True)

    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='services_likes')
    favorite_flagged = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='services_favorites')
    comments = models.ManyToManyField(Comment, blank=True, related_name='services_comments')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} by {self.provider.username}"


class ServiceDetailSection(models.Model):
    SECTION_TYPES = (
        ('text_image', 'Text with Image'),
        ('list', 'List View'),
        ('text_only', 'Text Only'),
        ('image_only', 'Image Only'),
    )

    service = models.ForeignKey('ServiceListing', on_delete=models.CASCADE, related_name='detail_sections')
    section_type = models.CharField(max_length=20, choices=SECTION_TYPES)
    order = models.PositiveIntegerField(default=0, help_text="Order in which sections appear")
    title = models.CharField(max_length=200, blank=True)

    content = models.TextField(blank=True)
    image = models.ImageField(upload_to='service_sections/', blank=True, null=True)

    list_items = models.JSONField(default=list, blank=True,
                                  help_text="JSON array of list items for list sections")

    def get_list_items(self):
        """Parse stored JSON list items"""
        try:
            return self.list_items if isinstance(self.list_items, list) else json.loads(self.list_items)
        except:
            return []

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.get_section_type_display()} section for {self.service.title}"
