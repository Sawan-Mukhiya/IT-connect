"""
Email students when an approved event matches their interests (category / event type).
"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mass_mail
from django.template.loader import render_to_string
from django.urls import reverse

from accounts.models import Event

User = get_user_model()

# Event.category values -> StudentInterest.interest codes (model choices)
EVENT_CATEGORY_TO_INTERESTS = {
    'tech': {
        'ai_ml', 'web_dev', 'mobile_dev', 'data_science', 'cloud',
        'cybersecurity', 'iot', 'blockchain', 'other',
    },
    'ai_ml': {'ai_ml'},
    'web': {'web_dev'},
    'mobile': {'mobile_dev'},
    'data': {'data_science'},
    'cloud': {'cloud'},
    'security': {'cybersecurity'},
    'iot': {'iot'},
    'blockchain': {'blockchain'},
    'other': {'other'},
}

# Legacy slugs saved by update_interests view -> canonical interest code
LEGACY_INTEREST_TO_CANONICAL = {
    'web-development': 'web_dev',
    'mobile-development': 'mobile_dev',
    'data-science': 'data_science',
    'artificial-intelligence': 'ai_ml',
    'cybersecurity': 'cybersecurity',
    'cloud-computing': 'cloud',
}

VALID_EVENT_TYPES = {'seminar', 'workshop', 'hackathon'}


def interest_codes_matching_event(event: Event) -> set:
    """StudentInterest.interest values that should receive a notification for this event."""
    codes = set(EVENT_CATEGORY_TO_INTERESTS.get(event.category, set()))
    if event.event_type in VALID_EVENT_TYPES:
        codes.add(event.event_type)

    expanded = set(codes)
    for legacy, canonical in LEGACY_INTEREST_TO_CANONICAL.items():
        if canonical in codes:
            expanded.add(legacy)
    return expanded


def students_to_notify_for_event(event: Event):
    """Users (students) with at least one matching interest and a usable email."""
    codes = interest_codes_matching_event(event)
    if not codes:
        return User.objects.none()

    return (
        User.objects.filter(
            user_type='student',
            interests__interest__in=codes,
        )
        .exclude(email__isnull=True)
        .exclude(email__exact='')
        .distinct()
    )


def send_event_interest_match_emails(event: Event) -> int:
    """
    Send one email per matching student. Returns number of messages queued/sent.
    Skips if no EMAIL_HOST configured and backend is not console (optional safety).
    """
    students = students_to_notify_for_event(event)
    if not students:
        return 0

    try:
        path = reverse('events:event_detail', kwargs={'event_id': event.id})
    except Exception:
        path = f'/events/{event.id}/'

    base = getattr(settings, 'SITE_BASE_URL', '').rstrip('/')
    event_url = f'{base}{path}' if base else path

    subject = f'New ITCONNECT event matches your interests: {event.title}'
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@itconnect.local')
    fail_silently = getattr(settings, 'EMAIL_FAIL_SILENTLY', settings.DEBUG)

    datatuples = []
    for user in students:
        body = render_to_string(
            'events/emails/student_event_match.txt',
            {
                'user': user,
                'event': event,
                'event_url': event_url,
            },
        ).strip()
        if user.email:
            datatuples.append((subject, body, from_email, [user.email]))

    if not datatuples:
        return 0

    send_mass_mail(datatuples, fail_silently=fail_silently)
    return len(datatuples)
