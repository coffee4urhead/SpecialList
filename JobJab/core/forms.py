import re

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model, forms
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.forms import ClearableFileInput, inlineformset_factory

from JobJab.core.models import TIMEZONE_CHOICES, UserOrganization, CustomUser, Certificate, BlacklistItem, \
    BlacklistReason

User = get_user_model()


class CleanUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email', "user_type", 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for fieldname in self.fields:
            self.fields[fieldname].help_text = None
            self.fields['password1'].help_text = "Your password must contain at least 10 characters."

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        # First check if passwords match (basic validation)
        if password1 and password2 and password1 != password2:
            raise ValidationError("Passwords don't match")

        # Then add your custom validation
        if len(password2) < 10:  # Changed to match your settings.py min_length
            raise ValidationError("Password must be at least 10 characters long.")
        if not re.search(r'[A-Z]', password2):
            raise ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r'[a-z]', password2):
            raise ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r'[0-9]', password2):
            raise ValidationError("Password must contain at least one number.")
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password2):
            raise ValidationError("Password must contain at least one special character.")

        return password2


class CleanLoginForm(AuthenticationForm):
    class CleanLoginForm(AuthenticationForm):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['username'].widget = forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            })
            self.fields['password'].widget = forms.PasswordInput(attrs={
                'class': 'form-control',
                'placeholder': 'Password'
            })

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username and password:
            from django.contrib.auth import authenticate
            user = authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError(
                    _("Invalid username or password."),
                    code='invalid_login',
                )
        return super().clean()

    class Meta:
        fields = ['username', 'password']


class CustomImageInput(ClearableFileInput):
    template_name = 'widgets/custom_clearable_file_input.html'


class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = [
            'first_name',
            'last_name',
            'email',
            'bio',
            'profile_picture',
            'backcover_profile',
            'phone_number',
            'profession',
            'personal_number',
            'timezone',
            'preferred_start',
            'preferred_end',
            'user_type',
        ]
        widgets = {
            'timezone': forms.Select(choices=TIMEZONE_CHOICES),
            'preferred_start': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'preferred_end': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4}),
            'profile_picture': CustomImageInput(attrs={'class': 'form-control-file'}),
            'backcover_profile': CustomImageInput(attrs={'class': 'form-control-file'}),
        }


class UserOrganizationForm(forms.ModelForm):
    class Meta:
        model = UserOrganization
        fields = ['organization', 'position', 'start_date', 'end_date', 'is_current']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


UserOrganizationFormSet = inlineformset_factory(
    parent_model=CustomUser,
    model=UserOrganization,
    form=UserOrganizationForm,
    extra=1,
    can_delete=True
)


class CertificateForm(forms.ModelForm):
    class Meta:
        model = Certificate
        fields = ['title', 'certificate_file']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Python Developer Certification'
            }),
            'certificate_file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf'
            })
        }
        help_texts = {
            'certificate_file': 'Only PDF files are accepted'
        }

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title and len(title) < 10:
            raise ValidationError("Certificate title must be at least 10 characters long")
        return title


class BlacklistItemForm(forms.ModelForm):
    reason = forms.ChoiceField(
        choices=BlacklistReason,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'aria-label': 'Select reason for reporting'
        }),
        help_text="Please select the most appropriate reason for reporting this content."
    )

    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Please provide specific details about why this content should be reviewed...'
        }),
        required=False,
        help_text="Additional details help us understand and process your report faster."
    )

    class Meta:
        model = BlacklistItem
        fields = ['reason', 'description']

    def __init__(self, *args, **kwargs):
        self.reported_object = kwargs.pop('reported_object', None)
        self.reporter = kwargs.pop('reporter', None)
        super().__init__(*args, **kwargs)

        self.fields['reason'].choices = BlacklistReason

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.reported_object:
            instance.content_object = self.reported_object

        if self.reporter:
            instance.reporter = self.reporter

        if commit:
            instance.save()

        return instance

    def _post_clean(self):
        if self.reported_object:
            self.instance.content_object = self.reported_object

        if self.reporter:
            self.instance.reporter = self.reporter

        super()._post_clean()

    def clean(self):
        cleaned_data = super().clean()

        if self.reported_object and self.reporter:
            if self.reported_object == self.reporter:
                raise forms.ValidationError("You cannot report your own content.")

            if hasattr(self.reported_object, 'user') and self.reported_object.user == self.reporter:
                raise forms.ValidationError("You cannot report your own content.")

        if len(cleaned_data.get('description', '').strip()) < 10:
            raise forms.ValidationError(
                "Please provide more details (at least 10 characters) about your report."
            )

        return cleaned_data
