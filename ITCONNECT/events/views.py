"""
Event Management Views
Handles event listing, creation, registration, and organizer dashboard
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from accounts.models import Event, Registration, OrganizerAnalytics, StudentInterest, StudentRecommendation
from .forms import EventForm


def event_list(request):
    """Public event listing page with filtering"""
    events = Event.objects.filter(status='active').order_by('date')

    # Filter by event type
    event_type = request.GET.get('type')
    if event_type:
        events = events.filter(event_type=event_type)

    # Filter by category
    category = request.GET.get('category')
    if category:
        events = events.filter(category=category)

    # Search by title/description
    search = request.GET.get('search')
    if search:
        events = events.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(organizer__username__icontains=search)
        )

    context = {
        'events': events,
        'event_types': Event.EVENT_TYPE_CHOICES,
        'categories': Event.CATEGORY_CHOICES,
        'current_filters': {
            'type': event_type,
            'category': category,
            'search': search,
        }
    }
    return render(request, 'events/event_list.html', context)


def event_detail(request, event_id):
    """Event detail page with registration option"""
    event = get_object_or_404(Event, id=event_id, status='active')

    # Check if user is registered
    is_registered = False
    user_registration = None
    if request.user.is_authenticated:
        try:
            user_registration = Registration.objects.get(user=request.user, event=event)
            is_registered = True
        except Registration.DoesNotExist:
            pass

    # Check if registration is still open
    registration_open = event.deadline > timezone.now() and event.available_seats > 0

    context = {
        'event': event,
        'is_registered': is_registered,
        'user_registration': user_registration,
        'registration_open': registration_open,
        'can_register': request.user.is_authenticated and not is_registered and registration_open,
    }
    return render(request, 'events/event_detail.html', context)


@login_required
def event_register(request, event_id):
    """Handle event registration"""
    event = get_object_or_404(Event, id=event_id, status='active')

    # Check if already registered
    if Registration.objects.filter(user=request.user, event=event).exists():
        messages.warning(request, 'You are already registered for this event.')
        return redirect('event_detail', event_id=event.id)

    # Check if registration is closed
    if event.deadline <= timezone.now():
        messages.error(request, 'Registration deadline has passed.')
        return redirect('event_detail', event_id=event.id)

    # Check if event is full
    if event.available_seats <= 0:
        messages.error(request, 'This event is fully booked.')
        return redirect('event_detail', event_id=event.id)

    if request.method == 'POST':
        # Create registration
        registration = Registration.objects.create(
            user=request.user,
            event=event,
            status='registered'
        )

        # Update student's enrollment count
        if hasattr(request.user, 'student_profile'):
            request.user.student_profile.event_enroll_count += 1
            request.user.student_profile.save()

        # Update event available seats
        event.available_seats -= 1
        event.save()

        messages.success(request, f'Successfully registered for {event.title}!')
        return redirect('event_detail', event_id=event.id)

    return redirect('event_detail', event_id=event.id)


@login_required
def event_unregister(request, event_id):
    """Handle event unregistration"""
    event = get_object_or_404(Event, id=event_id)
    registration = get_object_or_404(Registration, user=request.user, event=event)

    if request.method == 'POST':
        cancellation_reason = request.POST.get('cancellation_reason', '')

        # Update registration
        registration.status = 'cancelled'
        registration.cancellation_reason = cancellation_reason
        registration.save()

        # Update student's enrollment count
        if hasattr(request.user, 'student_profile'):
            request.user.student_profile.event_enroll_count -= 1
            request.user.student_profile.save()

        # Update event available seats
        event.available_seats += 1
        event.save()

        messages.success(request, f'Successfully cancelled registration for {event.title}.')
        return redirect('event_detail', event_id=event.id)

    return redirect('event_detail', event_id=event.id)


@login_required
def organizer_dashboard(request):
    """Organizer dashboard with event analytics"""
    if request.user.user_type != 'organizer':
        messages.error(request, 'Access denied. Organizer account required.')
        return redirect('home')

    # Get organizer's events
    events = Event.objects.filter(organizer=request.user).order_by('-created_at')

    # Calculate analytics
    total_events = events.count()
    active_events = events.filter(status='active').count()
    total_registrations = Registration.objects.filter(event__organizer=request.user).count()
    total_revenue = 0  # Will be calculated from payments

    # Recent registrations
    recent_registrations = Registration.objects.filter(
        event__organizer=request.user
    ).select_related('user', 'event').order_by('-registered_at')[:10]

    context = {
        'events': events,
        'total_events': total_events,
        'active_events': active_events,
        'total_registrations': total_registrations,
        'total_revenue': total_revenue,
        'recent_registrations': recent_registrations,
    }
    return render(request, 'events/organizer_dashboard.html', context)


@login_required
def create_event(request):
    """Create new event (organizer only)"""
    if request.user.user_type != 'organizer':
        messages.error(request, 'Access denied. Organizer account required.')
        return redirect('home')

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()

            messages.success(request, f'Event "{event.title}" created successfully!')
            return redirect('organizer_dashboard')
    else:
        form = EventForm()

    return render(request, 'events/create_event.html', {'form': form})


@login_required
def edit_event(request, event_id):
    """Edit existing event (organizer only)"""
    event = get_object_or_404(Event, id=event_id, organizer=request.user)

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, f'Event "{event.title}" updated successfully!')
            return redirect('organizer_dashboard')
    else:
        form = EventForm(instance=event)

    return render(request, 'events/edit_event.html', {'form': form, 'event': event})


@login_required
def student_dashboard(request):
    """Student dashboard with recommendations and registrations"""
    if request.user.user_type != 'student':
        messages.error(request, 'Access denied. Student account required.')
        return redirect('home')

    # Get student's registrations
    registrations = Registration.objects.filter(
        user=request.user
    ).select_related('event').order_by('-registered_at')

    # Get recommendations (placeholder for now)
    recommendations = StudentRecommendation.objects.filter(
        student=request.user
    ).select_related('recommended_event')[:5]

    # Get student's interests for display
    interests = StudentInterest.objects.filter(student=request.user)

    context = {
        'registrations': registrations,
        'recommendations': recommendations,
        'interests': interests,
    }
    return render(request, 'events/student_dashboard.html', context)


def generate_recommendations(request):
    """Generate personalized event recommendations for student"""
    if not request.user.is_authenticated or request.user.user_type != 'student':
        return redirect('home')

    # Get student's interests
    student_interests = StudentInterest.objects.filter(student=request.user).values_list('interest', flat=True)

    # Find events matching interests
    recommended_events = Event.objects.filter(
        status='active',
        category__in=student_interests
    ).exclude(
        registrations__user=request.user  # Exclude already registered events
    ).order_by('date')[:10]

    # Create recommendations
    for event in recommended_events:
        StudentRecommendation.objects.get_or_create(
            student=request.user,
            recommended_event=event,
            defaults={'reason': 'interest_match'}
        )

    messages.success(request, 'New event recommendations generated!')
    return redirect('student_dashboard')