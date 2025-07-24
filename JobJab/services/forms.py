import json

from django import forms
from django.forms import inlineformset_factory

from .models import ServiceListing, Availability, ServiceDetailSection, Comment


class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = Availability
        fields = ['date', 'start_time', 'end_time', 'status', 'note']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }


class ServiceListingForm(forms.ModelForm):
    class Meta:
        model = ServiceListing
        exclude = ['provider']

        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(),
        }

        labels = {
            'duration_minutes': 'Duration (minutes)',
            'service_photo': 'Service Image',
            'price': 'Price for the service',
            'is_active': 'Is active?',
        }


class ServiceDetailSectionForm(forms.ModelForm):
    list_items = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 5,
            'placeholder': 'Enter one item per line',
            'data-list-input': 'true'
        }),
        required=False
    )

    class Meta:
        model = ServiceDetailSection
        fields = ['section_type', 'order', 'title', 'content', 'image', 'list_items']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 3}),
            'order': forms.HiddenInput()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if not self.instance.pk:
            self.initial['section_type'] = 'text_image'

        for field in self.fields:
            self.fields[field].required = False

    def clean(self):
        cleaned_data = super().clean()
        section_type = cleaned_data.get('section_type')

        if section_type == 'list':
            raw_items = cleaned_data.get('list_items', '')

            if raw_items:
                try:
                    if raw_items.strip().startswith('['):
                        json.loads(raw_items)
                    else:
                        items = [item.strip() for item in raw_items.split('\n') if item.strip()]
                        cleaned_data['list_items'] = json.dumps(items)
                except json.JSONDecodeError:
                    self.add_error('list_items', 'Invalid list format')
            elif not self.instance.list_items:
                self.add_error('list_items', 'This field is required for list sections')
        elif section_type == 'text_image':
            if not cleaned_data.get('content'):
                self.add_error('content', 'This field is required for text+image sections')
            if not cleaned_data.get('image') and not self.instance.image:
                self.add_error('image', 'This field is required for text+image sections')
        return cleaned_data


ServiceDetailSectionFormSet = inlineformset_factory(
    parent_model=ServiceListing,
    model=ServiceDetailSection,
    form=ServiceDetailSectionForm,
    extra=1,
    can_delete=True,
    can_order=True,
    fields=['section_type', 'order', 'title', 'content', 'image', 'list_items']
)

class CommentForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'comment-input',
            'placeholder': 'Enter your comment...',
            'id': 'comment-input-field'
        })
    )

    class Meta:
        model = Comment
        fields = ['content']