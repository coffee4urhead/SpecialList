from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model, forms
from django import forms
from django.forms import ClearableFileInput, inlineformset_factory

from JobJab.core.models import TIMEZONE_CHOICES, UserOrganization, CustomUser

User = get_user_model()


class CleanUserCreationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for fieldname in self.fields:
            self.fields[fieldname].help_text = None
    class Meta:
        model = User
        fields = ('username', 'email', "user_type", 'password1', 'password2')

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
            'timezone'
        ]
        widgets = {
            'timezone': forms.Select(choices=TIMEZONE_CHOICES),
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