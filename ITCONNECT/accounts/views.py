from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from .forms import CustomUserCreationForm, AdminRegistrationForm, OrganizerRegistrationForm, StudentRegistrationForm
from .models import AdminProfile, OrganizerProfile, StudentProfile

class RegistrationView(FormView):
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('registration_success')
    
    def get_form_class(self):
        user_type = self.request.GET.get('user_type', 'student')
        if user_type == 'admin':
            return AdminRegistrationForm
        elif user_type == 'organizer':
            return OrganizerRegistrationForm
        else:
            return StudentRegistrationForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_type'] = self.request.GET.get('user_type', 'student')
        context['user_form'] = CustomUserCreationForm()
        return context
    
    def post(self, request, *args, **kwargs):
        user_form = CustomUserCreationForm(request.POST)
        profile_form = self.get_form_class()(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.user_type = request.GET.get('user_type', 'student')
            user.save()
            
            if user.user_type == 'admin':
                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()
            elif user.user_type == 'organizer':
                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()
            else:  # student
                profile = profile_form.save(commit=False)
                profile.user = user
                profile.save()
            
            login(request, user)
            messages.success(request, f'Account created successfully as {user.get_user_type_display()}!')
            return redirect('registration_success')
        
        return self.form_invalid(profile_form)

def registration_success(request):
    return render(request, 'accounts/registration_success.html')

def choose_registration_type(request):
    return render(request, 'accounts/choose_registration_type.html')
