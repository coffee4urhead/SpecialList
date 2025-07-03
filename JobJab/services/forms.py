from django import forms
from .models import ServiceListing


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