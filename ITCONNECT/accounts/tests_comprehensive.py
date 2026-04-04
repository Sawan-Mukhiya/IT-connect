"""
Comprehensive Application Tests
Tests all major user flows and functionality
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from accounts.models import Event, Registration, StudentProfile, OrganizerProfile, AdminProfile, StudentInterest
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


class ApplicationComprehensiveTests(TestCase):
    """Comprehensive tests for the entire application"""

    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test users
        self.student_user = User.objects.create_user(
            username='student1',
            email='student1@test.com',
            password='testpass123',
            user_type='student',
            first_name='John',
            last_name='Doe'
        )
        StudentProfile.objects.create(
            user=self.student_user,
            student_id='STU001',
            grade_level='Senior',
            graduation_year=2025
        )
        
        self.organizer_user = User.objects.create_user(
            username='organizer1',
            email='organizer1@test.com',
            password='testpass123',
            user_type='organizer',
            first_name='Jane',
            last_name='Smith'
        )
        OrganizerProfile.objects.create(
            user=self.organizer_user,
            organization_name='Tech Events Inc',
            organization_type='Tech Company'
        )
        
        self.admin_user = User.objects.create_user(
            username='admin1',
            email='admin1@test.com',
            password='testpass123',
            user_type='admin',
            first_name='Admin',
            last_name='User'
        )
        AdminProfile.objects.create(
            user=self.admin_user,
            department='Administration',
            employee_id='ADM001',
            permissions='[]'
        )
        
        # Create test event
        self.event = Event.objects.create(
            title='Test Seminar',
            description='This is a test seminar',
            organizer=self.organizer_user,
            event_type='seminar',
            category='tech',
            date=timezone.now() + timedelta(days=10),
            deadline=timezone.now() + timedelta(days=5),
            location='Online',
            seats=50,
            is_paid=False,
            is_approved=True,
            approved_by=self.admin_user,
            approved_at=timezone.now()
        )

    # ========== PUBLIC PAGE TESTS ==========
    def test_home_page(self):
        """Test home page is accessible"""
        response = self.client.get(reverse('accounts:home'))
        self.assertEqual(response.status_code, 200)
        print("[PASS] Home page loads successfully")

    def test_about_page(self):
        """Test about page is accessible"""
        response = self.client.get(reverse('accounts:about'))
        self.assertEqual(response.status_code, 200)
        print("[PASS] About page loads successfully")

    def test_contact_page(self):
        """Test contact page is accessible"""
        response = self.client.get(reverse('accounts:contact'))
        self.assertEqual(response.status_code, 200)
        print("[PASS] Contact page loads successfully")

    def test_event_list_page(self):
        """Test event listing page shows only approved events"""
        response = self.client.get(reverse('events:event_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.event, response.context['events'])
        print("[PASS] Event listing page shows approved events")

    # ========== AUTHENTICATION TESTS ==========
    def test_login_page(self):
        """Test login page is accessible"""
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        print("[PASS] Login page loads successfully")

    def test_registration_type_page(self):
        """Test registration type selection page"""
        response = self.client.get(reverse('accounts:choose_registration_type'))
        self.assertEqual(response.status_code, 200)
        print("[PASS] Registration type page loads successfully")

    def test_student_login(self):
        """Test student login"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'student1',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
        print("[PASS] Student login successful")

    def test_organizer_login(self):
        """Test organizer login"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'organizer1',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        print("[PASS] Organizer login successful")

    def test_admin_login(self):
        """Test admin login"""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'admin1',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)
        print("[PASS] Admin login successful")

    # ========== STUDENT TESTS ==========
    def test_student_dashboard(self):
        """Test student can access dashboard"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('events:student_dashboard'))
        self.assertEqual(response.status_code, 200)
        print("[PASS] Student dashboard loads successfully")

    def test_student_can_register_for_event(self):
        """Test student can register for approved event"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.post(reverse('events:event_register', args=[self.event.id]))
        self.assertEqual(response.status_code, 302)  # Redirect after registration
        
        # Check registration was created
        self.assertTrue(Registration.objects.filter(
            user=self.student_user,
            event=self.event
        ).exists())
        print("[PASS] Student can register for events")

    def test_student_cannot_register_twice(self):
        """Test student cannot register for same event twice"""
        self.client.login(username='student1', password='testpass123')
        
        # First registration
        self.client.post(reverse('events:event_register', args=[self.event.id]))
        
        # Second registration attempt
        response = self.client.post(reverse('events:event_register', args=[self.event.id]))
        self.assertEqual(response.status_code, 302)
        
        # Only one registration should exist
        registrations = Registration.objects.filter(
            user=self.student_user,
            event=self.event
        )
        self.assertEqual(registrations.count(), 1)
        print("[PASS] Student cannot register twice for same event")

    def test_student_can_unregister(self):
        """Test student can unregister from event"""
        self.client.login(username='student1', password='testpass123')
        
        # Register first
        Registration.objects.create(
            user=self.student_user,
            event=self.event,
            status='registered'
        )
        
        # Unregister
        response = self.client.post(reverse('events:event_unregister', args=[self.event.id]))
        self.assertEqual(response.status_code, 302)
        print("[PASS] Student can unregister from events")

    def test_update_interests(self):
        """Test student can update interests"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('events:update_interests'))
        self.assertEqual(response.status_code, 200)
        print("[PASS] Student interest update page loads")

    # ========== ORGANIZER TESTS ==========
    def test_organizer_dashboard(self):
        """Test organizer can access dashboard"""
        self.client.login(username='organizer1', password='testpass123')
        response = self.client.get(reverse('events:organizer_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.event, response.context['events'])
        print("[PASS] Organizer dashboard loads successfully")

    def test_organizer_create_event(self):
        """Test organizer can create event"""
        self.client.login(username='organizer1', password='testpass123')
        response = self.client.get(reverse('events:create_event'))
        self.assertEqual(response.status_code, 200)
        print("[PASS] Event creation page loads")

    def test_organizer_edit_event(self):
        """Test organizer can edit their event"""
        self.client.login(username='organizer1', password='testpass123')
        response = self.client.get(reverse('events:edit_event', args=[self.event.id]))
        self.assertEqual(response.status_code, 200)
        print("[PASS] Event editing page loads")

    def test_organizer_delete_event(self):
        """Test organizer can delete their event"""
        self.client.login(username='organizer1', password='testpass123')
        event_id = self.event.id
        response = self.client.post(reverse('events:delete_event', args=[event_id]))
        self.assertEqual(response.status_code, 302)
        
        # Check event was deleted
        self.assertFalse(Event.objects.filter(id=event_id).exists())
        print("[PASS] Organizer can delete events")

    def test_organizer_cannot_delete_others_event(self):
        """Test organizer cannot delete other's event"""
        other_organizer = User.objects.create_user(
            username='organizer2',
            email='organizer2@test.com',
            password='testpass123',
            user_type='organizer'
        )
        OrganizerProfile.objects.create(
            user=other_organizer,
            organization_name='Other Org',
            organization_type='Other'
        )
        
        self.client.login(username='organizer2', password='testpass123')
        response = self.client.post(reverse('events:delete_event', args=[self.event.id]))
        self.assertEqual(response.status_code, 404)
        print("[PASS] Organizer cannot delete other's event")

    # ========== ADMIN TESTS ==========
    def test_admin_pending_events(self):
        """Test admin can see pending events"""
        # Create unapproved event
        unapproved = Event.objects.create(
            title='Unapproved Event',
            description='This is unapproved',
            organizer=self.organizer_user,
            event_type='workshop',
            category='tech',
            date=timezone.now() + timedelta(days=15),
            deadline=timezone.now() + timedelta(days=10),
            location='Lab',
            seats=30,
            is_paid=False,
            is_approved=False
        )
        
        self.client.login(username='admin1', password='testpass123')
        response = self.client.get(reverse('events:admin_pending_events'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(unapproved, response.context['pending_events'])
        print("[PASS] Admin can see pending events")

    def test_admin_approve_event(self):
        """Test admin can approve event"""
        unapproved = Event.objects.create(
            title='To Approve',
            description='Approve me',
            organizer=self.organizer_user,
            event_type='seminar',
            category='tech',
            date=timezone.now() + timedelta(days=20),
            deadline=timezone.now() + timedelta(days=15),
            location='Hall',
            seats=40,
            is_paid=False,
            is_approved=False
        )
        
        self.client.login(username='admin1', password='testpass123')
        response = self.client.post(reverse('events:approve_event', args=[unapproved.id]))
        self.assertEqual(response.status_code, 302)
        
        # Check event is approved
        unapproved.refresh_from_db()
        self.assertTrue(unapproved.is_approved)
        self.assertEqual(unapproved.approved_by, self.admin_user)
        print("[PASS] Admin can approve events")

    def test_admin_reject_event(self):
        """Test admin can reject event"""
        unapproved = Event.objects.create(
            title='To Reject',
            description='Reject me',
            organizer=self.organizer_user,
            event_type='hackathon',
            category='tech',
            date=timezone.now() + timedelta(days=25),
            deadline=timezone.now() + timedelta(days=20),
            location='Stadium',
            seats=100,
            is_paid=False,
            is_approved=False
        )
        
        self.client.login(username='admin1', password='testpass123')
        response = self.client.post(reverse('events:reject_event', args=[unapproved.id]), {
            'rejection_reason': 'Event details are incomplete'
        })
        self.assertEqual(response.status_code, 302)
        
        # Check event is cancelled
        unapproved.refresh_from_db()
        self.assertEqual(unapproved.status, 'cancelled')
        print("[PASS] Admin can reject events")

    # ========== NAVIGATION TESTS ==========
    def test_navigation_links_for_unauthenticated(self):
        """Test navigation shows correct links for unauthenticated users"""
        response = self.client.get(reverse('accounts:home'))
        self.assertContains(response, 'Login')
        self.assertContains(response, 'Register')
        self.assertContains(response, 'Browse Events')
        print("[PASS] Unauthenticated navigation shows login/register")

    def test_navigation_links_for_student(self):
        """Test navigation shows correct links for student"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('accounts:home'))
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'Logout')
        print("[PASS] Student navigation shows dashboard/logout")

    def test_navigation_links_for_organizer(self):
        """Test navigation shows correct links for organizer"""
        self.client.login(username='organizer1', password='testpass123')
        response = self.client.get(reverse('accounts:home'))
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'Logout')
        print("[PASS] Organizer navigation shows dashboard/logout")

    def test_navigation_links_for_admin(self):
        """Test navigation shows correct links for admin"""
        self.client.login(username='admin1', password='testpass123')
        response = self.client.get(reverse('accounts:home'))
        self.assertContains(response, 'Approve Events')
        self.assertContains(response, 'Admin Panel')
        self.assertContains(response, 'Logout')
        print("[PASS] Admin navigation shows approve/admin panel")

    # ========== EVENT VISIBILITY TESTS ==========
    def test_unapproved_event_not_visible_to_students(self):
        """Test unapproved events don't show in student event list"""
        unapproved = Event.objects.create(
            title='Secret Event',
            description='Not approved',
            organizer=self.organizer_user,
            event_type='seminar',
            category='tech',
            date=timezone.now() + timedelta(days=30),
            deadline=timezone.now() + timedelta(days=25),
            location='Secret',
            seats=10,
            is_paid=False,
            is_approved=False
        )
        
        response = self.client.get(reverse('events:event_list'))
        self.assertNotIn(unapproved, response.context['events'])
        print("[PASS] Unapproved events hidden from student listing")

    def test_approved_event_visible_to_students(self):
        """Test approved events show in student event list"""
        response = self.client.get(reverse('events:event_list'))
        self.assertIn(self.event, response.context['events'])
        print("[PASS] Approved events visible in student listing")

    # ========== PERMISSION TESTS ==========
    def test_student_cannot_access_organizer_dashboard(self):
        """Test student cannot access organizer dashboard"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('events:organizer_dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirect
        print("[PASS] Student cannot access organizer dashboard")

    def test_student_cannot_access_admin_dashboard(self):
        """Test student cannot access admin approval dashboard"""
        self.client.login(username='student1', password='testpass123')
        response = self.client.get(reverse('events:admin_pending_events'))
        self.assertEqual(response.status_code, 302)
        print("[PASS] Student cannot access admin dashboard")

    def test_organizer_cannot_access_admin_dashboard(self):
        """Test organizer cannot access admin approval dashboard"""
        self.client.login(username='organizer1', password='testpass123')
        response = self.client.get(reverse('events:admin_pending_events'))
        self.assertEqual(response.status_code, 302)
        print("[PASS] Organizer cannot access admin dashboard")
