from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic.edit import FormView
from django.views import View
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import (
    CustomUserCreationForm,
    AdminRegistrationForm,
    OrganizerRegistrationForm,
    StudentRegistrationForm,
    CustomAuthenticationForm,
    StudentUserProfileForm,
    StudentAcademicProfileForm,
)
from .models import AdminProfile, OrganizerProfile, StudentProfile, User, Team, Registration

class RegistrationView(FormView):
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('accounts:registration_success')
    
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
        # Django superusers should go to admin dashboard
        if user.is_superuser or user.user_type == 'admin':
            return reverse_lazy('events:admin_pending_events')
        elif user.user_type == 'organizer':
            return reverse_lazy('events:organizer_dashboard')
        elif user.user_type == 'student':
            return reverse_lazy('events:student_dashboard')
        else:
            # Default to admin dashboard for unrecognized users
            return reverse_lazy('events:admin_pending_events')

    def form_valid(self, form):
        user = form.get_user()
        messages.success(self.request, f'Welcome back, {user.get_full_name() or user.username}!')
        return super().form_valid(form)

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:home')

def landing_page(request):
    return render(request, 'landing.html')

def choose_registration_type(request):
    return render(request, 'accounts/choose_registration_type.html')

def about_page(request):
    return render(request, 'about.html')

def contact_page(request):
    return render(request, 'contact.html')


class StudentProfileView(LoginRequiredMixin, View):
    """Single student profile page: public view for others, inline edit for the owner."""
    template_name = 'accounts/student_profile.html'

    def get_student(self, username):
        return get_object_or_404(User, username=username, user_type='student')

    def build_context(self, request, student, user_form=None, profile_form=None, profile_edit_open=False):
        profile = student.student_profile
        skills_by_level = {}
        for skill in student.skills.all():
            level = skill.get_level_display()
            skills_by_level.setdefault(level, []).append(skill)

        registrations = Registration.objects.filter(user=student, status='registered')
        is_own = request.user.is_authenticated and request.user == student

        context = {
            'student': student,
            'profile': profile,
            'skills_by_level': skills_by_level,
            'interests': student.interests.all(),
            'achievements': student.achievements.all()[:6],
            'total_achievements': student.achievements.count(),
            'teams': Team.objects.filter(
                members__user=student
            ).select_related('event', 'team_lead').distinct(),
            'led_teams': student.led_teams.all().select_related('event').count(),
            'registered_events': registrations.count(),
            'recent_events': [r.event for r in registrations.order_by('-registered_at')[:3]],
            'is_own_profile': is_own,
            'profile_edit_open': profile_edit_open,
        }

        if is_own and hasattr(student, 'student_profile'):
            if user_form is None:
                user_form = StudentUserProfileForm(instance=student)
            if profile_form is None:
                profile_form = StudentAcademicProfileForm(instance=student.student_profile)
            context['user_form'] = user_form
            context['profile_form'] = profile_form

        return context

    def get(self, request, username):
        student = self.get_student(username)
        open_edit = request.GET.get('edit') == '1'
        ctx = self.build_context(request, student, profile_edit_open=open_edit)
        return render(request, self.template_name, ctx)

    def post(self, request, username):
        student = self.get_student(username)
        if request.user != student or not hasattr(student, 'student_profile'):
            messages.error(request, "You can't edit this profile.")
            return redirect('accounts:student_profile', username=username)

        user_form = StudentUserProfileForm(request.POST, request.FILES, instance=student)
        profile_form = StudentAcademicProfileForm(request.POST, instance=student.student_profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated.')
            return redirect('accounts:student_profile', username=student.username)

        ctx = self.build_context(
            request, student, user_form=user_form, profile_form=profile_form, profile_edit_open=True
        )
        return render(request, self.template_name, ctx)
