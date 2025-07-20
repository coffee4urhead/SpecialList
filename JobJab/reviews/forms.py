from django import forms
from django.core.exceptions import ValidationError

from .models import UserReview, WebsiteReview


class UserReviewForm(forms.ModelForm):
    reviewee_display = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly'})
    )

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

    def clean(self):
        cleaned_data = super().clean()
        if not self.reviewer:
            raise ValidationError("Reviews must have a reviewer")
        if not self.reviewee:
            raise ValidationError("Reviews must have a reviewee")
        if self.reviewer == self.reviewee:
            raise ValidationError("Cannot review yourself")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.reviewer = self.reviewer
        instance.reviewee = self.reviewee

        if commit:
            instance.save()
        return instance


class WebsiteReviewForm(forms.ModelForm):
    class Meta:
        model = WebsiteReview
        fields = ['rating', 'main_caption', 'comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Share your experience with our platform...'
            }),
            'main_caption': forms.TextInput(attrs={
                'maxlength': 30,
                'placeholder': 'Brief summary of your review'
            }),
            'rating': forms.NumberInput(attrs={
                'min': 1,
                'max': 5,
                'class': 'rating-input'
            })
        }

    def __init__(self, *args, **kwargs):
        self.reviewer = kwargs.pop('reviewer', None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()
        if not self.reviewer:
            raise ValidationError("You must be logged in to leave a review")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.reviewer = self.reviewer

        instance.full_clean()

        if commit:
            instance.save()
        return instance