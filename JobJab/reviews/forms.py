# reviews/forms.py
from django import forms
from .models import UserReview


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
            'main-caption': forms.TextInput(attrs={'maxlength': 30}),
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5})
        }

    def __init__(self, *args, **kwargs):
        self.reviewee = kwargs.get('reviewee', None)
        self.reviewer = kwargs.get('reviewer', None)
        super().__init__(*args, **kwargs)

        if self.reviewee:
            self.fields['reviewee_display'].initial = str(self.reviewee)

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.reviewee = self.reviewee
        instance.reviewer = self.reviewer
        if commit:
            instance.save()
        return instance
