from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse_lazy
from django.db.models import Q
from datetime import timedelta
import uuid

from accounts.models import Team, TeamMember, TeamJoinRequest, TeamInvitation, Event, Notification, User
from .forms import (
    CreateTeamForm, EditTeamForm, JoinTeamRequestForm, InviteMemberForm,
    ManageJoinRequestForm
)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_team_code():
    """Generate unique 8-character team code"""
    return str(uuid.uuid4())[:8].upper()


def create_notification(user, notification_type, message, event=None):
    """Create a notification for a user"""
    Notification.objects.create(
        user=user,
        notification_type=notification_type,
        message=message,
        event=event
    )


# ============================================================================
# TEAM LIST & DISCOVERY VIEWS
# ============================================================================

class TeamsHomeView(LoginRequiredMixin, View):
    """Unified teams home page with Find Teams and My Teams"""
    
    def get(self, request):
        user = request.user
        
        # Get public teams for discovery
        public_teams = Team.objects.filter(
            visibility='public',
            event__is_approved=True
        ).select_related('event', 'team_lead')
        
        # Apply search and filters
        search = request.GET.get('search', '')
        if search:
            public_teams = public_teams.filter(team_name__icontains=search)
        
        event_id = request.GET.get('event')
        if event_id:
            public_teams = public_teams.filter(event_id=event_id)
        
        public_teams = public_teams.order_by('-created_at')[:6]  # Show 6 recent teams
        
        # Get user's teams
        user_teams = Team.objects.filter(
            members__user=user
        ).select_related('event', 'team_lead').distinct()
        
        led_teams = Team.objects.filter(team_lead=user)
        
        # Get pending requests and invitations
        pending_requests = TeamJoinRequest.objects.filter(
            team__team_lead=user,
            status='pending'
        ).select_related('team', 'user')
        
        pending_invitations = TeamInvitation.objects.filter(
            invited_user=user,
            status='pending'
        ).select_related('team', 'invited_by')
        
        events = Event.objects.filter(
            event_type='hackathon',
            is_approved=True
        )
        
        context = {
            'public_teams': public_teams,
            'user_teams': user_teams,
            'led_teams': led_teams,
            'pending_requests': pending_requests,
            'pending_invitations': pending_invitations,
            'events': events,
            'search_query': search,
        }
        
        return render(request, 'teams/teams_home.html', context)


class TeamListView(LoginRequiredMixin, ListView):
    """Public team listing and discovery"""
    model = Team
    template_name = 'teams/team_list.html'
    context_object_name = 'teams'
    paginate_by = 12
    
    def get_queryset(self):
        """Get public teams from approved hackathons"""
        queryset = Team.objects.filter(
            visibility='public',
            event__is_approved=True
        ).select_related('event', 'team_lead')
        
        # Filter by event if specified
        event_id = self.request.GET.get('event')
        if event_id:
            queryset = queryset.filter(event_id=event_id)
        
        # Search by team name
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(team_name__icontains=search)
        
        # Filter by member count
        min_members = self.request.GET.get('min_members')
        if min_members:
            queryset = [team for team in queryset if team.get_current_member_count() >= int(min_members)]
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['events'] = Event.objects.filter(
            event_type='hackathon',
            is_approved=True
        )
        context['search_query'] = self.request.GET.get('search', '')
        return context


class TeamDetailView(LoginRequiredMixin, DetailView):
    """View team details"""
    model = Team
    template_name = 'teams/team_detail.html'
    context_object_name = 'team'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.get_object()
        user = self.request.user
        
        # Team members and relationships
        context['members'] = team.members.all().select_related('user')
        context['is_member'] = team.members.filter(user=user).exists()
        context['is_leader'] = team.team_lead == user
        
        # Request/Invitation status
        context['pending_request'] = team.join_requests.filter(
            user=user,
            status='pending'
        ).first()
        context['pending_invitation'] = team.invitations.filter(
            invited_user=user,
            status='pending'
        ).first()
        
        # Can user join?
        context['can_join'] = (
            not context['is_member'] and
            not context['is_leader'] and
            not team.is_full() and
            not context['pending_request'] and
            not context['pending_invitation'] and
            not team.event.teams.filter(members__user=user).exists()
        )
        
        # Available students for invitation (not already members)
        if context['is_leader']:
            team_members = team.members.values_list('user_id', flat=True)
            context['available_students'] = User.objects.filter(
                user_type='student'
            ).exclude(id__in=team_members).order_by('username')
            context['pending_join_requests'] = team.join_requests.filter(
                status='pending'
            ).select_related('user')
        else:
            context['pending_join_requests'] = team.join_requests.none()
        
        return context


class MyTeamsView(LoginRequiredMixin, ListView):
    """View teams user is part of"""
    model = Team
    template_name = 'teams/my_teams.html'
    context_object_name = 'teams'
    paginate_by = 12
    
    def get_queryset(self):
        """Get teams user is member of"""
        user = self.request.user
        return Team.objects.filter(
            members__user=user
        ).select_related('event', 'team_lead').distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        context['led_teams'] = Team.objects.filter(
            team_lead=user
        ).select_related('event')
        
        context['pending_requests'] = TeamJoinRequest.objects.filter(
            team__team_lead=user,
            status='pending'
        ).select_related('team', 'user')
        
        context['pending_invitations'] = TeamInvitation.objects.filter(
            invited_user=user,
            status='pending'
        ).select_related('team', 'invited_by')
        
        return context


# ============================================================================
# TEAM CREATION & MANAGEMENT VIEWS
# ============================================================================

class CreateTeamView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new team"""
    model = Team
    form_class = CreateTeamForm
    template_name = 'teams/create_team.html'
    
    def test_func(self):
        """Only students can create teams"""
        return self.request.user.user_type == 'student'
    
    def form_valid(self, form):
        team = form.save(commit=False)
        team.team_lead = self.request.user
        team.team_code = generate_team_code()
        team.save()
        
        # Add creator as team member with leader role
        TeamMember.objects.create(
            team=team,
            user=self.request.user,
            role='leader'
        )
        
        messages.success(self.request, f'Team "{team.team_name}" created successfully!')
        return redirect('teams:team_detail', pk=team.pk)
    
    def get_success_url(self):
        return reverse_lazy('teams:team_detail', kwargs={'pk': self.object.pk})


class EditTeamView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Edit team details"""
    model = Team
    form_class = EditTeamForm
    template_name = 'teams/edit_team.html'
    
    def test_func(self):
        """Only team leader can edit"""
        team = self.get_object()
        return self.request.user == team.team_lead
    
    def form_valid(self, form):
        messages.success(self.request, 'Team updated successfully!')
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('teams:team_detail', kwargs={'pk': self.object.pk})


class DeleteTeamView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a team"""
    model = Team
    template_name = 'teams/delete_team.html'
    success_url = reverse_lazy('teams:my_teams')
    
    def test_func(self):
        """Only team leader can delete"""
        team = self.get_object()
        return self.request.user == team.team_lead
    
    def delete(self, request, *args, **kwargs):
        team = self.get_object()
        team_name = team.team_name
        messages.success(request, f'Team "{team_name}" has been deleted.')
        return super().delete(request, *args, **kwargs)


# ============================================================================
# JOIN REQUEST VIEWS
# ============================================================================

class RequestToJoinView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Request to join a team"""
    
    def test_func(self):
        """Only students can request to join"""
        return self.request.user.user_type == 'student'
    
    def post(self, request, team_id):
        team = get_object_or_404(Team, id=team_id)
        user = request.user
        
        # Validation
        if team.members.filter(user=user).exists():
            messages.error(request, 'You are already a member of this team.')
            return redirect('teams:team_detail', pk=team.id)
        
        if team.join_requests.filter(user=user, status='pending').exists():
            messages.error(request, 'You already have a pending request for this team.')
            return redirect('teams:team_detail', pk=team.id)
        
        if team.is_full():
            messages.error(request, 'This team is full.')
            return redirect('teams:team_detail', pk=team.id)
        
        # Check if user is already in another team for same event
        if team.event.teams.filter(members__user=user).exists():
            messages.error(request, 'You are already in another team for this event.')
            return redirect('teams:team_detail', pk=team.id)
        
        # Create join request
        message = request.POST.get('message', '')
        join_request = TeamJoinRequest.objects.create(
            team=team,
            user=user,
            message=message
        )
        
        # Notify team leader
        create_notification(
            team.team_lead,
            'team_join_request',
            f'{user.username} requested to join your team "{team.team_name}"',
            team.event
        )
        
        messages.success(request, 'Request to join sent! Waiting for leader approval.')
        return redirect('teams:team_detail', pk=team.id)


class JoinRequestListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """View join requests for team (leader only)"""
    model = TeamJoinRequest
    template_name = 'teams/join_requests.html'
    context_object_name = 'requests'
    paginate_by = 20
    
    def test_func(self):
        """Only team leader can view requests"""
        team_id = self.kwargs.get('team_id')
        team = get_object_or_404(Team, id=team_id)
        return self.request.user == team.team_lead
    
    def get_queryset(self):
        team_id = self.kwargs.get('team_id')
        return TeamJoinRequest.objects.filter(
            team_id=team_id,
            status='pending'
        ).select_related('user')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team_id = self.kwargs.get('team_id')
        context['team'] = get_object_or_404(Team, id=team_id)
        return context


class AcceptJoinRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Accept a join request"""
    
    def test_func(self):
        """Only team leader can accept"""
        request_obj = get_object_or_404(TeamJoinRequest, id=self.kwargs.get('request_id'))
        return self.request.user == request_obj.team.team_lead
    
    def get(self, request, request_id):
        join_request = get_object_or_404(TeamJoinRequest, id=request_id)
        team = join_request.team
        user = join_request.user
        
        # Check if team is full
        if team.is_full():
            messages.error(request, 'Team is full. Cannot accept more members.')
            return redirect('teams:join_requests', team_id=team.id)
        
        # Add user to team
        TeamMember.objects.create(team=team, user=user, role='member')
        
        # Update join request
        join_request.status = 'accepted'
        join_request.responded_at = timezone.now()
        join_request.save()
        
        # Notify user
        create_notification(
            user,
            'team_join_request_accepted',
            f'Your request to join "{team.team_name}" has been accepted!',
            team.event
        )
        
        # Notify all team members
        for member in team.members.all():
            if member.user != join_request.user:
                create_notification(
                    member.user,
                    'team_member_joined',
                    f'{user.username} joined your team "{team.team_name}"',
                    team.event
                )
        
        messages.success(request, f'{user.username} has been added to the team!')
        return redirect('teams:join_requests', team_id=team.id)


class RejectJoinRequestView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Reject a join request"""
    
    def test_func(self):
        request_obj = get_object_or_404(TeamJoinRequest, id=self.kwargs.get('request_id'))
        return self.request.user == request_obj.team.team_lead
    
    def post(self, request, request_id):
        join_request = get_object_or_404(TeamJoinRequest, id=request_id)
        team = join_request.team
        user = join_request.user
        
        response_message = request.POST.get('response_message', '')
        
        join_request.status = 'rejected'
        join_request.responded_at = timezone.now()
        join_request.response_message = response_message
        join_request.save()
        
        # Notify user
        message = f'Your request to join "{team.team_name}" has been rejected.'
        if response_message:
            message += f' Reason: {response_message}'
        
        create_notification(
            user,
            'team_join_request_rejected',
            message,
            team.event
        )
        
        messages.success(request, 'Join request rejected.')
        return redirect('teams:join_requests', team_id=team.id)


# ============================================================================
# INVITATION VIEWS
# ============================================================================

class InviteMemberView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Invite a student to join team"""
    
    def test_func(self):
        team_id = self.kwargs.get('team_id')
        team = get_object_or_404(Team, id=team_id)
        return self.request.user == team.team_lead
    
    def post(self, request, team_id):
        team = get_object_or_404(Team, id=team_id)
        invited_user_id = request.POST.get('invited_user')
        message = request.POST.get('message', '')
        
        try:
            invited_user = self.request.user.__class__.objects.get(id=invited_user_id)
        except self.request.user.__class__.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('teams:team_detail', pk=team.id)
        
        # Validation
        if invited_user == request.user:
            messages.error(request, 'You cannot invite yourself.')
            return redirect('teams:team_detail', pk=team.id)
        
        if team.members.filter(user=invited_user).exists():
            messages.error(request, 'User is already a member of this team.')
            return redirect('teams:team_detail', pk=team.id)
        
        if team.invitations.filter(invited_user=invited_user, status='pending').exists():
            messages.error(request, 'User already has a pending invitation.')
            return redirect('teams:team_detail', pk=team.id)
        
        if team.is_full():
            messages.error(request, 'Team is full.')
            return redirect('teams:team_detail', pk=team.id)
        
        # Create invitation
        invitation = TeamInvitation.objects.create(
            team=team,
            invited_user=invited_user,
            invited_by=request.user,
            message=message,
            expires_at=timezone.now() + timedelta(days=7)
        )
        
        # Notify invited user
        create_notification(
            invited_user,
            'team_invitation',
            f'{request.user.username} invited you to join team "{team.team_name}"',
            team.event
        )
        
        messages.success(request, f'Invitation sent to {invited_user.username}!')
        return redirect('teams:team_detail', pk=team.id)


class AcceptInvitationView(LoginRequiredMixin, View):
    """Accept team invitation"""
    
    def get(self, request, invitation_id):
        invitation = get_object_or_404(TeamInvitation, id=invitation_id)
        team = invitation.team
        user = request.user
        
        # Validation
        if invitation.invited_user != user:
            messages.error(request, 'This invitation is not for you.')
            return redirect('teams:team_detail', pk=team.id)
        
        if invitation.status != 'pending':
            messages.error(request, 'This invitation is no longer valid.')
            return redirect('teams:team_detail', pk=team.id)
        
        if timezone.now() > invitation.expires_at:
            messages.error(request, 'This invitation has expired.')
            return redirect('teams:my_teams')
        
        if team.is_full():
            messages.error(request, 'This team is now full.')
            return redirect('teams:team_detail', pk=team.id)
        
        if team.event.teams.filter(members__user=user).exists():
            messages.error(request, 'You are already in another team for this event.')
            return redirect('teams:team_detail', pk=team.id)
        
        # Add user to team
        TeamMember.objects.create(team=team, user=user, role='member')
        
        # Update invitation
        invitation.status = 'accepted'
        invitation.responded_at = timezone.now()
        invitation.save()
        
        # Notify team leader
        create_notification(
            team.team_lead,
            'team_invitation_accepted',
            f'{user.username} accepted your invitation to join "{team.team_name}"',
            team.event
        )
        
        # Notify team members
        for member in team.members.all():
            if member.user != user:
                create_notification(
                    member.user,
                    'team_member_joined',
                    f'{user.username} joined your team "{team.team_name}"',
                    team.event
                )
        
        messages.success(request, f'You joined "{team.team_name}"!')
        return redirect('teams:team_detail', pk=team.id)


class RejectInvitationView(LoginRequiredMixin, View):
    """Reject team invitation"""
    
    def get(self, request, invitation_id):
        invitation = get_object_or_404(TeamInvitation, id=invitation_id)
        
        if invitation.invited_user != request.user:
            messages.error(request, 'This invitation is not for you.')
            return redirect('teams:my_teams')
        
        if invitation.status != 'pending':
            messages.error(request, 'This invitation is no longer valid.')
            return redirect('teams:my_teams')
        
        team = invitation.team
        invitation.status = 'rejected'
        invitation.responded_at = timezone.now()
        invitation.save()
        
        # Notify team leader
        create_notification(
            team.team_lead,
            'team_invitation_rejected',
            f'{request.user.username} rejected your invitation to join "{team.team_name}"',
            team.event
        )
        
        messages.success(request, 'Invitation rejected.')
        return redirect('teams:my_teams')


# ============================================================================
# MEMBER MANAGEMENT VIEWS
# ============================================================================

class RemoveMemberView(LoginRequiredMixin, UserPassesTestMixin, View):
    """Remove member from team (leader only)"""
    
    def test_func(self):
        member_id = self.kwargs.get('member_id')
        member = get_object_or_404(TeamMember, id=member_id)
        return self.request.user == member.team.team_lead
    
    def post(self, request, member_id):
        member = get_object_or_404(TeamMember, id=member_id)
        team = member.team
        user = member.user
        
        if user == team.team_lead:
            messages.error(request, 'You cannot remove the team leader.')
            return redirect('teams:team_detail', pk=team.id)
        
        member.delete()
        
        # Notify removed member
        create_notification(
            user,
            'team_member_left',
            f'You have been removed from team "{team.team_name}"',
            team.event
        )
        
        messages.success(request, f'{user.username} has been removed from the team.')
        return redirect('teams:team_detail', pk=team.id)


class LeaveTeamView(LoginRequiredMixin, View):
    """Leave a team (member only)"""
    
    def post(self, request, team_id):
        team = get_object_or_404(Team, id=team_id)
        
        if request.user == team.team_lead:
            messages.error(request, 'Team leader cannot leave. Disband the team instead.')
            return redirect('teams:team_detail', pk=team.id)
        
        member = get_object_or_404(TeamMember, team=team, user=request.user)
        member.delete()
        
        # Notify team leader
        create_notification(
            team.team_lead,
            'team_member_left',
            f'{request.user.username} left team "{team.team_name}"',
            team.event
        )
        
        messages.success(request, f'You left "{team.team_name}".')
        return redirect('teams:my_teams')
