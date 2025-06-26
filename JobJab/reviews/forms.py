from django import forms
from django.core.exceptions import ValidationError

from .models import UserReview
from ..core.models import CustomUser


class UserReviewForm(forms.ModelForm):
    reviewee_display = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )
    reviewer_id = forms.IntegerField(widget=forms.HiddenInput())

    class Meta:
        model = UserReview
        fields = ['rating', 'main_caption', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={'rows': 4}),
            'main_caption': forms.TextInput(attrs={'maxlength': 30}),
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5})
        }

    def __init__(self, *args, **kwargs):
        self.reviewee = kwargs.pop('reviewee', None)
        self.reviewer = kwargs.pop('reviewer', None)
        super().__init__(*args, **kwargs)

        if self.reviewee:
            self.fields['reviewee_display'].initial = str(self.reviewee)
        if self.reviewer:
            self.fields['reviewer_id'].initial = self.reviewer.id

    def clean(self):
        cleaned_data = super().clean()

        # Get reviewer from form data
        reviewer_id = cleaned_data.get('reviewer_id')
        if not reviewer_id:
            raise ValidationError("Reviewer is required")

        try:
            self.reviewer = CustomUser.objects.get(id=reviewer_id)
        except (CustomUser.DoesNotExist, ValueError):
            raise ValidationError("Invalid reviewer specified")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.reviewee = self.reviewee
        instance._reviewer = self.reviewer

        if commit:
            instance.save()

        return instance