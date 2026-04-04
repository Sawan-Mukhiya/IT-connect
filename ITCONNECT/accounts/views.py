from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.contrib.auth.views import LoginView
from .forms import CustomUserCreationForm, AdminRegistrationForm, OrganizerRegistrationForm, StudentRegistrationForm, CustomAuthenticationForm
from .models import AdminProfile, OrganizerProfile, StudentProfile

class RegistrationView(FormView):
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('registration_success')
    
    def get_user_type(self):
        return self.request.GET.get('user_type', 'student')

    def get_form_class(self):
        user_type = self.get_user_type()
        if user_type == 'admin':
            return AdminRegistrationForm
        elif user_type == 'organizer':
            return OrganizerRegistrationForm
        else:
            return StudentRegistrationForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_type = self.get_user_type()
        context['user_type'] = user_type
        if self.request.method == 'POST':
            context['user_form'] = CustomUserCreationForm(self.request.POST)
            context['profile_form'] = self.get_form_class()(self.request.POST)
        else:
            context['user_form'] = CustomUserCreationForm()
            context['profile_form'] = self.get_form_class()()
        return context

    def form_valid(self, form):
        user_form = CustomUserCreationForm(self.request.POST)
        profile_form = form

        if not user_form.is_valid():
            return self.form_invalid(form)

        user = user_form.save(commit=False)
        user.user_type = self.get_user_type()
        user.save()

        profile = profile_form.save(commit=False)
        profile.user = user
        profile.save()

        login(self.request, user)
        messages.success(self.request, f'Account created successfully as {user.get_user_type_display()}!')
        return super().form_valid(form)

def registration_success(request):
    return render(request, 'accounts/registration_success.html')

class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'
    form_class = CustomAuthenticationForm
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if user.user_type == 'organizer':
            return reverse_lazy('events:organizer_dashboard')
        elif user.user_type == 'student':
            return reverse_lazy('events:student_dashboard')
        else:  # admin
            return reverse_lazy('admin:index')

    def form_valid(self, form):
        messages.success(self.request, f'Welcome back, {self.request.user.get_full_name() or self.request.user.username}!')
        return super().form_valid(form)

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('home')

def landing_page(request):
    return render(request, 'landing.html')

def choose_registration_type(request):
    return render(request, 'accounts/choose_registration_type.html')

def about_page(request):
    return render(request, 'about.html')

def contact_page(request):
    return render(request, 'contact.html')
