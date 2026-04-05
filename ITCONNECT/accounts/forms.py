from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User, AdminProfile, OrganizerProfile, StudentProfile

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=False)
    user_type = forms.ChoiceField(choices=User.USER_TYPE_CHOICES)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'user_type', 'password1', 'password2')

class CustomAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or Email'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=20, required=False)
    user_type = forms.ChoiceField(choices=User.USER_TYPE_CHOICES)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'user_type', 'password1', 'password2')

class AdminRegistrationForm(forms.ModelForm):
    class Meta:
        model = AdminProfile
        fields = ['department', 'employee_id', 'permissions']
        widgets = {
            'permissions': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter permissions as JSON format'})
        }

class OrganizerRegistrationForm(forms.ModelForm):
    class Meta:
        model = OrganizerProfile
        fields = ['organization_name', 'organization_type', 'license_number', 'website']

class StudentRegistrationForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['student_id', 'grade_level', 'major', 'graduation_year', 'gpa']
        widgets = {
            'graduation_year': forms.NumberInput(attrs={'min': 2020, 'max': 2030})
        }


class StudentUserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'spf-input', 'autocomplete': 'given-name'}),
            'last_name': forms.TextInput(attrs={'class': 'spf-input', 'autocomplete': 'family-name'}),
            'email': forms.EmailInput(attrs={'class': 'spf-input', 'autocomplete': 'email'}),
            'phone_number': forms.TextInput(attrs={'class': 'spf-input', 'autocomplete': 'tel'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'spf-file'}),
        }

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip()
        if not email:
            raise ValidationError('Email is required.')
        qs = User.objects.filter(email__iexact=email)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('This email is already in use.')
        return email


class StudentAcademicProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['student_id', 'grade_level', 'major', 'graduation_year', 'gpa']
        widgets = {
            'student_id': forms.TextInput(attrs={'class': 'spf-input'}),
            'grade_level': forms.TextInput(attrs={'class': 'spf-input', 'placeholder': 'e.g. Sophomore'}),
            'major': forms.TextInput(attrs={'class': 'spf-input'}),
            'graduation_year': forms.NumberInput(attrs={'class': 'spf-input', 'min': 2020, 'max': 2040}),
            'gpa': forms.NumberInput(attrs={'class': 'spf-input', 'min': 0, 'max': 4, 'step': '0.01'}),
        }

    def clean_student_id(self):
        student_id = (self.cleaned_data.get('student_id') or '').strip()
        if not student_id:
            raise ValidationError('Student ID is required.')
        qs = StudentProfile.objects.filter(student_id__iexact=student_id)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError('This student ID is already registered.')
        return student_id
