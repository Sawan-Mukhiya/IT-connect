"""
Integration tests for Teams feature
Tests all team-related workflows including creation, joining, requests, and invitations
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta

from accounts.models import User, Event, Team, TeamMember, TeamJoinRequest, TeamInvitation


class TeamCreationTestCase(TestCase):
    """Test team creation functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create students
        self.student1 = User.objects.create_user(
            username='student1',
            email='s1@test.com',
            password='test123',
            user_type='student'
        )
        
        self.student2 = User.objects.create_user(
            username='student2',
            email='s2@test.com',
            password='test123',
            user_type='student'
        )
        
        # Create event
        self.event = Event.objects.create(
            title='Hackathon 2026',
            description='Test hackathon',
            organizer=User.objects.create_user(
                username='organizer',
                email='org@test.com',
                password='test123',
                user_type='organizer'
            ),
            event_type='hackathon',
            category='tech',
            date=timezone.now() + timedelta(days=30),
            deadline=timezone.now() + timedelta(days=20),
            seats=100,
            is_approved=True
        )
    
    def test_student_can_create_team(self):
        """Test that a student can create a team"""
        self.client.login(username='student1', password='test123')
        
        response = self.client.post(reverse('teams:create_team'), {
            'team_name': 'Team Alpha',
            'description': 'A great team',
            'event': self.event.id,
            'max_members': 4,
            'visibility': 'public'
        })
        
        # Should redirect to team detail
        self.assertEqual(response.status_code, 302)
        
        # Team should be created
        team = Team.objects.get(team_name='Team Alpha')
        self.assertEqual(team.team_lead, self.student1)
        self.assertEqual(team.max_members, 4)
        self.assertEqual(team.visibility, 'public')
        
        # Creator should be added as leader
        self.assertTrue(team.members.filter(user=self.student1).exists())
    
    def test_team_name_validation(self):
        """Test team name validation"""
        self.client.login(username='student1', password='test123')
        
        # Too short
        response = self.client.post(reverse('teams:create_team'), {
            'team_name': 'AB',
            'event': self.event.id,
            'max_members': 4,
            'visibility': 'public'
        })
        # Form should have errors
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('team_name', form.errors)
    
    def test_non_student_cannot_create_team(self):
        """Test that non-students cannot create teams"""
        # Organizer cannot create team
        self.client.login(username='organizer', password='test123')
        response = self.client.get(reverse('teams:create_team'))
        self.assertEqual(response.status_code, 403)


class TeamJoinRequestTestCase(TestCase):
    """Test join request functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create students
        self.leader = User.objects.create_user(
            username='leader',
            email='leader@test.com',
            password='test123',
            user_type='student'
        )
        
        self.student = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='test123',
            user_type='student'
        )
        
        # Create event
        self.event = Event.objects.create(
            title='Hackathon 2026',
            description='Test hackathon',
            organizer=User.objects.create_user(
                username='organizer',
                email='org@test.com',
                password='test123',
                user_type='organizer'
            ),
            event_type='hackathon',
            category='tech',
            date=timezone.now() + timedelta(days=30),
            deadline=timezone.now() + timedelta(days=20),
            seats=100,
            is_approved=True
        )
        
        # Create team
        self.team = Team.objects.create(
            team_name='Team Alpha',
            team_lead=self.leader,
            event=self.event,
            max_members=4,
            visibility='public'
        )
        
        # Add leader as member
        TeamMember.objects.create(team=self.team, user=self.leader, role='leader')
    
    def test_student_can_request_to_join(self):
        """Test that a student can request to join a team"""
        self.client.login(username='student', password='test123')
        
        response = self.client.post(reverse('teams:request_join', args=[self.team.id]), {
            'message': 'I want to join your team'
        })
        
        # Should be redirected
        self.assertEqual(response.status_code, 302)
        
        # Request should be created
        self.assertTrue(TeamJoinRequest.objects.filter(
            team=self.team,
            user=self.student,
            status='pending'
        ).exists())
    
    def test_leader_can_accept_request(self):
        """Test that team leader can accept join requests"""
        # Create request
        request_obj = TeamJoinRequest.objects.create(
            team=self.team,
            user=self.student,
            message='I want to join',
            status='pending'
        )
        
        self.client.login(username='leader', password='test123')
        response = self.client.get(reverse('teams:accept_join_request', args=[request_obj.id]))
        
        # Should be redirected
        self.assertEqual(response.status_code, 302)
        
        # Request status should be accepted
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, 'accepted')
        
        # Student should be added as member
        self.assertTrue(self.team.members.filter(user=self.student).exists())
    
    def test_leader_can_reject_request(self):
        """Test that team leader can reject join requests"""
        # Create request
        request_obj = TeamJoinRequest.objects.create(
            team=self.team,
            user=self.student,
            status='pending'
        )
        
        self.client.login(username='leader', password='test123')
        response = self.client.post(reverse('teams:reject_join_request', args=[request_obj.id]), {
            'response_message': 'Team is full'
        })
        
        # Should be redirected
        self.assertEqual(response.status_code, 302)
        
        # Request status should be rejected
        request_obj.refresh_from_db()
        self.assertEqual(request_obj.status, 'rejected')
        self.assertEqual(request_obj.response_message, 'Team is full')
    
    def test_cannot_request_twice(self):
        """Test that student cannot request twice"""
        # First request
        TeamJoinRequest.objects.create(
            team=self.team,
            user=self.student,
            status='pending'
        )
        
        self.client.login(username='student', password='test123')
        response = self.client.post(reverse('teams:request_join', args=[self.team.id]), {})
        
        # Should still be 302 redirect, but no new request should be created
        # Count requests from this user for this team
        count = TeamJoinRequest.objects.filter(
            team=self.team,
            user=self.student
        ).count()
        self.assertEqual(count, 1)  # Still just the original one
    
    def test_cannot_join_if_team_full(self):
        """Test that student cannot join a full team"""
        # Add members till team is full
        for i in range(3):
            user = User.objects.create_user(
                username=f'member{i}',
                email=f'member{i}@test.com',
                password='test123',
                user_type='student'
            )
            TeamMember.objects.create(team=self.team, user=user)
        
        self.client.login(username='student', password='test123')
        response = self.client.post(reverse('teams:request_join', args=[self.team.id]), {})
        
        # Request should NOT be created for full team
        self.assertFalse(TeamJoinRequest.objects.filter(
            team=self.team,
            user=self.student
        ).exists())


class TeamInvitationTestCase(TestCase):
    """Test team invitation functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create students
        self.leader = User.objects.create_user(
            username='leader',
            email='leader@test.com',
            password='test123',
            user_type='student'
        )
        
        self.student = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='test123',
            user_type='student'
        )
        
        # Create event
        self.event = Event.objects.create(
            title='Hackathon 2026',
            description='Test hackathon',
            organizer=User.objects.create_user(
                username='organizer',
                email='org@test.com',
                password='test123',
                user_type='organizer'
            ),
            event_type='hackathon',
            category='tech',
            date=timezone.now() + timedelta(days=30),
            deadline=timezone.now() + timedelta(days=20),
            seats=100,
            is_approved=True
        )
        
        # Create team
        self.team = Team.objects.create(
            team_name='Team Alpha',
            team_lead=self.leader,
            event=self.event,
            max_members=4
        )
        
        # Add leader as member
        TeamMember.objects.create(team=self.team, user=self.leader, role='leader')
    
    def test_leader_can_invite_member(self):
        """Test that team leader can invite members"""
        self.client.login(username='leader', password='test123')
        
        response = self.client.post(reverse('teams:invite_member', args=[self.team.id]), {
            'invited_user': self.student.id,
            'message': 'Join our team!'
        })
        
        # Invitation should be created
        self.assertTrue(TeamInvitation.objects.filter(
            team=self.team,
            invited_user=self.student,
            status='pending'
        ).exists())
    
    def test_student_can_accept_invitation(self):
        """Test that invited student can accept invitation"""
        # Create invitation
        invitation = TeamInvitation.objects.create(
            team=self.team,
            invited_user=self.student,
            invited_by=self.leader,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        self.client.login(username='student', password='test123')
        response = self.client.get(reverse('teams:accept_invitation', args=[invitation.id]))
        
        # Should be redirected
        self.assertEqual(response.status_code, 302)
        
        # Student should be added to team
        self.assertTrue(self.team.members.filter(user=self.student).exists())
        
        # Invitation status should be accepted
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, 'accepted')
    
    def test_student_can_reject_invitation(self):
        """Test that invited student can reject invitation"""
        # Create invitation
        invitation = TeamInvitation.objects.create(
            team=self.team,
            invited_user=self.student,
            invited_by=self.leader,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        self.client.login(username='student', password='test123')
        response = self.client.get(reverse('teams:reject_invitation', args=[invitation.id]))
        
        # Should be redirected
        self.assertEqual(response.status_code, 302)
        
        # Invitation should be rejected
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, 'rejected')
        
        # Student should not be in team
        self.assertFalse(self.team.members.filter(user=self.student).exists())
    
    def test_cannot_accept_expired_invitation(self):
        """Test that student cannot accept expired invitation"""
        # Create expired invitation
        invitation = TeamInvitation.objects.create(
            team=self.team,
            invited_user=self.student,
            invited_by=self.leader,
            expires_at=timezone.now() - timedelta(days=1)  # Expired
        )
        
        self.client.login(username='student', password='test123')
        response = self.client.get(reverse('teams:accept_invitation', args=[invitation.id]))
        
        # Invitation should still be pending (not accepted)
        invitation.refresh_from_db()
        self.assertEqual(invitation.status, 'pending')
        
        # Student should NOT be in team
        self.assertFalse(self.team.members.filter(user=self.student).exists())


class TeamMembershipTestCase(TestCase):
    """Test team membership functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create students
        self.leader = User.objects.create_user(
            username='leader',
            email='leader@test.com',
            password='test123',
            user_type='student'
        )
        
        self.member = User.objects.create_user(
            username='member',
            email='member@test.com',
            password='test123',
            user_type='student'
        )
        
        # Create event
        self.event = Event.objects.create(
            title='Hackathon 2026',
            description='Test hackathon',
            organizer=User.objects.create_user(
                username='organizer',
                email='org@test.com',
                password='test123',
                user_type='organizer'
            ),
            event_type='hackathon',
            category='tech',
            date=timezone.now() + timedelta(days=30),
            deadline=timezone.now() + timedelta(days=20),
            seats=100,
            is_approved=True
        )
        
        # Create team
        self.team = Team.objects.create(
            team_name='Team Alpha',
            team_lead=self.leader,
            event=self.event,
            max_members=4
        )
        
        # Add members
        TeamMember.objects.create(team=self.team, user=self.leader, role='leader')
        TeamMember.objects.create(team=self.team, user=self.member, role='member')
    
    def test_member_can_leave_team(self):
        """Test that member can leave team"""
        self.client.login(username='member', password='test123')
        
        response = self.client.post(reverse('teams:leave_team', args=[self.team.id]))
        
        # Should be redirected
        self.assertEqual(response.status_code, 302)
        
        # Member should be removed
        self.assertFalse(self.team.members.filter(user=self.member).exists())
    
    def test_leader_can_remove_member(self):
        """Test that leader can remove member"""
        member_obj = self.team.members.get(user=self.member)
        
        self.client.login(username='leader', password='test123')
        response = self.client.post(reverse('teams:remove_member', args=[member_obj.id]))
        
        # Should be redirected
        self.assertEqual(response.status_code, 302)
        
        # Member should be removed
        self.assertFalse(self.team.members.filter(user=self.member).exists())
    
    def test_leader_cannot_leave_team(self):
        """Test that leader cannot leave team"""
        self.client.login(username='leader', password='test123')
        
        response = self.client.post(reverse('teams:leave_team', args=[self.team.id]))
        
        # Leader should STILL be in team (leave failed)
        self.assertTrue(self.team.members.filter(user=self.leader).exists())


class OneStudentPerEventConstraintTestCase(TestCase):
    """Test that students can only be in one team per event"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create students
        self.student = User.objects.create_user(
            username='student',
            email='student@test.com',
            password='test123',
            user_type='student'
        )
        
        self.leader1 = User.objects.create_user(
            username='leader1',
            email='leader1@test.com',
            password='test123',
            user_type='student'
        )
        
        self.leader2 = User.objects.create_user(
            username='leader2',
            email='leader2@test.com',
            password='test123',
            user_type='student'
        )
        
        # Create event
        self.event = Event.objects.create(
            title='Hackathon 2026',
            description='Test hackathon',
            organizer=User.objects.create_user(
                username='organizer',
                email='org@test.com',
                password='test123',
                user_type='organizer'
            ),
            event_type='hackathon',
            category='tech',
            date=timezone.now() + timedelta(days=30),
            deadline=timezone.now() + timedelta(days=20),
            seats=100,
            is_approved=True
        )
        
        # Create two teams for same event
        self.team1 = Team.objects.create(
            team_name='Team Alpha',
            team_lead=self.leader1,
            event=self.event,
            max_members=4
        )
        
        self.team2 = Team.objects.create(
            team_name='Team Beta',
            team_lead=self.leader2,
            event=self.event,
            max_members=4
        )
        
        # Add leaders
        TeamMember.objects.create(team=self.team1, user=self.leader1, role='leader')
        TeamMember.objects.create(team=self.team2, user=self.leader2, role='leader')
        
        # Add student to team1
        TeamMember.objects.create(team=self.team1, user=self.student, role='member')
    
    def test_student_cannot_join_another_team_same_event(self):
        """Test that student cannot join another team in the same event"""
        self.client.login(username='student', password='test123')
        
        response = self.client.post(reverse('teams:request_join', args=[self.team2.id]), {})
        
        # Request should NOT be created
        self.assertFalse(TeamJoinRequest.objects.filter(
            team=self.team2,
            user=self.student
        ).exists())
