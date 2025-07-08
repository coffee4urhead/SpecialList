from django import forms
from django.core.exceptions import ValidationError
from datetime import datetime, time
from .models import (
    ProviderAvailability,
    WeeklyTimeSlot,
    Booking,
    BookingStatus
)
from ..services.models import ServiceListing


class ProviderAvailabilityForm(forms.ModelForm):
    class Meta:
        model = ProviderAvailability
        exclude = ('provider',)
        widgets = {
            'slot_duration': forms.NumberInput(attrs={'min': 15, 'step': 15}),
            'buffer_time': forms.NumberInput(attrs={'min': 0}),
        }

    def clean_slot_duration(self):
        duration = self.cleaned_data['slot_duration']
        if duration % 15 != 0:
            raise ValidationError("Slot duration must be in 15-minute increments (15, 30, 45, etc.)")
        return duration

class WeeklyTimeSlotForm(forms.ModelForm):
    class Meta:
        model = WeeklyTimeSlot
        fields = ['day_of_week', 'start_time', 'end_time', 'is_booked']
        widgets = {
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
            'is_booked': forms.CheckboxInput(attrs={'checked': False}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            raise ValidationError("End time must be after start time")

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ['service', 'appointment_datetime', 'notes', 'time_slot']
        widgets = {
            'appointment_datetime': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'min': datetime.now().strftime("%Y-%m-%dT%H:%M")
                }
            ),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.provider = kwargs.pop('provider', None)
        super().__init__(*args, **kwargs)
        if self.provider:
            self.fields['service'].queryset = ServiceListing.objects.filter(provider=self.provider)

    def clean_appointment_datetime(self):
        appointment = self.cleaned_data['appointment_datetime']
        if appointment < datetime.now():
            raise ValidationError("Appointment cannot be in the past")
        return appointment