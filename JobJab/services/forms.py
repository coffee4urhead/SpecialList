from django import forms
from .models import ServiceListing, Availability, ServiceCategory


#Will not be used for now!
class ServiceCategoryForm(forms.ModelForm):
    class Meta:
        model = ServiceCategory
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

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