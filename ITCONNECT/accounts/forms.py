from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
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
