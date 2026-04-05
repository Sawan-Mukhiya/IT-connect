"""
Event Management Views
Handles event listing, creation, registration, and organizer dashboard
"""

import logging

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.utils import timezone
from accounts.models import Event, Registration, OrganizerAnalytics, StudentInterest, StudentRecommendation
from .forms import EventForm
from .interest_notifications import send_event_interest_match_emails

logger = logging.getLogger(__name__)


def event_list(request):
    """Public event listing page with filtering - only approved events"""
    events = Event.objects.filter(status='active', is_approved=True).order_by('-created_at')

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
    """Event detail page with registration option - only approved events"""
    # Allow viewing if: approved, or user is organizer/admin of the event
    event = get_object_or_404(Event, id=event_id, status='active')
    
    # Check authorization
    is_organizer_or_admin = (request.user.is_authenticated and 
                            (event.organizer == request.user or request.user.user_type == 'admin' or request.user.is_superuser))
    
    if not event.is_approved and not is_organizer_or_admin:
        messages.error(request, 'This event is not yet approved for public viewing.')
        return redirect('events:event_list')

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
        'can_register': request.user.is_authenticated and request.user.user_type == 'student' and not is_registered and registration_open,
    }
    return render(request, 'events/event_detail.html', context)


@login_required
def event_register(request, event_id):
    """Handle event registration - only students can register"""
    # Check if user is a student
    if request.user.user_type != 'student':
        messages.error(request, 'Only students can register for events. Please log in as a student.')
        return redirect('events:event_detail', event_id=event_id)
    
    event = get_object_or_404(Event, id=event_id, status='active', is_approved=True)

    # Check if already registered
    if Registration.objects.filter(user=request.user, event=event).exists():
        messages.warning(request, 'You are already registered for this event.')
        return redirect('events:event_detail', event_id=event.id)

    # Check if registration is closed
    if event.deadline <= timezone.now():
        messages.error(request, 'Registration deadline has passed.')
        return redirect('events:event_detail', event_id=event.id)

    # Check if event is full
    if event.available_seats <= 0:
        messages.error(request, 'This event is fully booked.')
        return redirect('events:event_detail', event_id=event.id)

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
        return redirect('events:event_detail', event_id=event.id)

    return redirect('events:event_detail', event_id=event.id)


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
        return redirect('events:event_detail', event_id=event.id)

    return redirect('events:event_detail', event_id=event.id)


@login_required
def organizer_dashboard(request):
    """Organizer dashboard with event analytics"""
    if request.user.user_type != 'organizer':
        messages.error(request, 'Access denied. Organizer account required.')
        return redirect('accounts:home')

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
        return redirect('accounts:home')

    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()

            messages.success(request, f'Event "{event.title}" created successfully!')
            return redirect('events:organizer_dashboard')
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
            return redirect('events:organizer_dashboard')
    else:
        form = EventForm(instance=event)

    return render(request, 'events/edit_event.html', {'form': form, 'event': event})


@login_required
def delete_event(request, event_id):
    """Delete an event (organizer only)"""
    event = get_object_or_404(Event, id=event_id, organizer=request.user)

    if request.method == 'POST':
        event_title = event.title
        event.delete()
        messages.success(request, f'Event "{event_title}" has been deleted successfully!')
        return redirect('events:organizer_dashboard')

    return redirect('events:organizer_dashboard')


@login_required
def student_dashboard(request):
    """Student dashboard with recommendations and registrations"""
    if request.user.user_type != 'student':
        messages.error(request, 'Access denied. Student account required.')
        return redirect('accounts:home')

    # Get all student's registrations
    all_registrations = Registration.objects.filter(
        user=request.user
    ).select_related('event').order_by('-registered_at')

    # Separate registrations by status
    now = timezone.now()
    registered_events = all_registrations.filter(status='registered')
    upcoming_events = registered_events.filter(event__date__gt=now)
    completed_events = registered_events.filter(event__date__lt=now)

    # Get recommendations
    recommendations = StudentRecommendation.objects.filter(
        student=request.user
    ).select_related('recommended_event')[:5]

    # Calculate total spent on events
    total_spent = 0
    for registration in registered_events:
        if registration.event.is_paid:
            total_spent += registration.event.price

    context = {
        'registered_events': registered_events,
        'upcoming_events': upcoming_events,
        'completed_events': completed_events,
        'recommendations': recommendations,
        'total_spent': total_spent,
        'now': now,
    }
    return render(request, 'events/student_dashboard.html', context)


def generate_recommendations(request):
    """Generate personalized event recommendations for student"""
    if not request.user.is_authenticated or request.user.user_type != 'student':
        return redirect('accounts:home')

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
    return redirect('events:student_dashboard')


@login_required
def update_interests(request):
    """Update student's interests"""
    if request.user.user_type != 'student':
        messages.error(request, 'Access denied. Student account required.')
        return redirect('accounts:home')

    # Define available interests
    INTERESTS = [
        ('web-development', 'Web Development', '🌐'),
        ('mobile-development', 'Mobile Development', '📱'),
        ('data-science', 'Data Science', '📊'),
        ('artificial-intelligence', 'AI & Machine Learning', '🤖'),
        ('cybersecurity', 'Cybersecurity', '🔒'),
        ('cloud-computing', 'Cloud Computing', '☁️'),
        ('entrepreneurship', 'Entrepreneurship', '💼'),
        ('product-management', 'Product Management', '📦'),
        ('ux-ui-design', 'UX/UI Design', '🎨'),
        ('marketing', 'Marketing', '📢'),
        ('sales', 'Sales', '💰'),
        ('business-analytics', 'Business Analytics', '📈'),
        ('public-speaking', 'Public Speaking', '🎤'),
        ('career-development', 'Career Development', '📚'),
        ('networking', 'Networking', '🤝'),
        ('personal-development', 'Personal Development', '💡'),
    ]

    # Get current user's interests
    user_interests = StudentInterest.objects.filter(student=request.user).values_list('interest', flat=True)
    selected_interests = list(user_interests)

    if request.method == 'POST':
        selected = request.POST.getlist('interests')
        
        # Clear existing interests
        StudentInterest.objects.filter(student=request.user).delete()
        
        # Add new interests
        for interest in selected:
            StudentInterest.objects.create(student=request.user, interest=interest)
        
        messages.success(request, f'Your interests have been updated! You selected {len(selected)} interests.')
        return redirect('events:student_dashboard')

    context = {
        'interests': INTERESTS,
        'selected_interests': selected_interests,
    }
    return render(request, 'events/update_interests.html', context)


# ============================================================================
# ADMIN EVENT APPROVAL VIEWS
# ============================================================================

@login_required
def admin_pending_events(request):
    """Admin dashboard for approving pending events"""
    if request.user.user_type != 'admin' and not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin account required.')
        return redirect('accounts:home')

    # Get pending events (not approved)
    pending_events = Event.objects.filter(is_approved=False).order_by('-created_at')
    approved_events = Event.objects.filter(is_approved=True).order_by('-approved_at')

    context = {
        'pending_events': pending_events,
        'approved_events': approved_events,
    }
    return render(request, 'events/admin_pending_events.html', context)


@login_required
def approve_event(request, event_id):
    """Approve an event for public viewing"""
    if request.user.user_type != 'admin' and not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin account required.')
        return redirect('accounts:home')

    event = get_object_or_404(Event, id=event_id)
    was_approved = event.is_approved

    # Handle GET request - approve immediately
    if request.method == 'GET':
        event.is_approved = True
        event.approved_by = request.user
        event.approved_at = timezone.now()
        event.save()
        if not was_approved and event.status == 'active':
            try:
                n = send_event_interest_match_emails(event)
                if n:
                    messages.info(request, f'Interest-match notifications sent to {n} student(s).')
            except Exception:
                logger.exception('Interest-match email failed for event %s', event.id)
                messages.warning(
                    request,
                    'Event approved, but interest notifications could not be sent (check email settings).',
                )
        messages.success(request, f'Event "{event.title}" has been approved!')
        return redirect('events:admin_pending_events')

    # Handle POST request - show confirmation page
    if request.method == 'POST':
        event.is_approved = True
        event.approved_by = request.user
        event.approved_at = timezone.now()
        event.save()
        if not was_approved and event.status == 'active':
            try:
                n = send_event_interest_match_emails(event)
                if n:
                    messages.info(request, f'Interest-match notifications sent to {n} student(s).')
            except Exception:
                logger.exception('Interest-match email failed for event %s', event.id)
                messages.warning(
                    request,
                    'Event approved, but interest notifications could not be sent (check email settings).',
                )
        messages.success(request, f'Event "{event.title}" has been approved!')
        return redirect('events:admin_pending_events')

    context = {'event': event}
    return render(request, 'events/approve_event.html', context)


@login_required
def reject_event(request, event_id):
    """Reject an event (move to cancelled status)"""
    if request.user.user_type != 'admin' and not request.user.is_superuser:
        messages.error(request, 'Access denied. Admin account required.')
        return redirect('accounts:home')

    event = get_object_or_404(Event, id=event_id)

    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '')
        event.status = 'cancelled'
        event.save()
        
        messages.success(request, f'Event "{event.title}" has been rejected.')
        # TODO: Send notification to organizer with rejection_reason
        return redirect('events:admin_pending_events')

    context = {'event': event}
    return render(request, 'events/reject_event.html', context)