"""
Forms for Event Management
"""

from django import forms
from django.utils import timezone
from accounts.models import Event


class EventForm(forms.ModelForm):
    """Form for creating and editing events"""

    class Meta:
        model = Event
        fields = [
            'title', 'description', 'event_type', 'category',
            'date', 'deadline', 'location', 'seats', 'is_paid', 'price', 'image'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter event title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your event'
            }),
            'event_type': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'deadline': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Event location or "Virtual"'
            }),
            'seats': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'step': '0.01'
            }),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date and date <= timezone.now():
            raise forms.ValidationError("Event date must be in the future.")
        return date

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        date = self.cleaned_data.get('date')

        if deadline and date and deadline >= date:
            raise forms.ValidationError("Registration deadline must be before the event date.")

        if deadline and deadline <= timezone.now():
            raise forms.ValidationError("Registration deadline must be in the future.")

        return deadline

    def clean_price(self):
        is_paid = self.cleaned_data.get('is_paid')
        price = self.cleaned_data.get('price')

        if is_paid and (price is None or price <= 0):
            raise forms.ValidationError("Paid events must have a price greater than 0.")

        if not is_paid and price and price > 0:
            raise forms.ValidationError("Free events cannot have a price.")

        return price