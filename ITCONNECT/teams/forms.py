from django import forms
from accounts.models import Team, TeamJoinRequest, TeamInvitation, User, Event
from django.core.exceptions import ValidationError


class CreateTeamForm(forms.ModelForm):
    """Form for creating a new team"""
    event = forms.ModelChoiceField(
        queryset=Event.objects.filter(event_type='hackathon', is_approved=True),
        label='Select Hackathon Event',
        help_text='Choose the hackathon event for your team'
    )
    
    class Meta:
        model = Team
        fields = ['team_name', 'description', 'event', 'max_members', 'visibility']
        widgets = {
            'team_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter team name',
                'maxlength': 200
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Team description and goals',
                'rows': 4
            }),
            'event': forms.Select(attrs={
                'class': 'form-control'
            }),
            'max_members': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2,
                'max': 10,
                'value': 4
            }),
            'visibility': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def clean_team_name(self):
        """Validate team name"""
        team_name = self.cleaned_data.get('team_name', '').strip()
        
        if len(team_name) < 3:
            raise ValidationError('Team name must be at least 3 characters long.')
        
        if len(team_name) > 50:
            raise ValidationError('Team name must not exceed 50 characters.')
        
        # Check for special characters
        if not team_name.replace(' ', '').isalnum():
            raise ValidationError('Team name can only contain letters, numbers, and spaces.')
        
        return team_name
    
    def clean_max_members(self):
        """Validate max members"""
        max_members = self.cleaned_data.get('max_members')
        
        if max_members < 2:
            raise ValidationError('Team must have at least 2 members.')
        
        if max_members > 10:
            raise ValidationError('Team cannot have more than 10 members.')
        
        return max_members


class EditTeamForm(forms.ModelForm):
    """Form for editing team details"""
    
    class Meta:
        model = Team
        fields = ['team_name', 'description', 'max_members', 'visibility']
        widgets = {
            'team_name': forms.TextInput(attrs={
                'class': 'form-control',
                'maxlength': 200
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4
            }),
            'max_members': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 2,
                'max': 10
            }),
            'visibility': forms.Select(attrs={
                'class': 'form-control'
            }),
        }
    
    def clean_team_name(self):
        """Validate team name"""
        team_name = self.cleaned_data.get('team_name', '').strip()
        
        if len(team_name) < 3:
            raise ValidationError('Team name must be at least 3 characters long.')
        
        if len(team_name) > 50:
            raise ValidationError('Team name must not exceed 50 characters.')
        
        if not team_name.replace(' ', '').isalnum():
            raise ValidationError('Team name can only contain letters, numbers, and spaces.')
        
        return team_name


class JoinTeamRequestForm(forms.ModelForm):
    """Form for requesting to join a team"""
    
    class Meta:
        model = TeamJoinRequest
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Why do you want to join this team? (Optional)',
                'rows': 4
            }),
        }


class InviteMemberForm(forms.ModelForm):
    """Form for inviting a member to team"""
    invited_user = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type='student'),
        label='Select Student to Invite'
    )
    
    class Meta:
        model = TeamInvitation
        fields = ['invited_user', 'message']
        widgets = {
            'invited_user': forms.Select(attrs={
                'class': 'form-control'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Invitation message (Optional)',
                'rows': 3
            }),
        }
    
    def __init__(self, *args, team=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.team = team
        
        # Filter to show only students not already in the team
        if team:
            team_members = team.members.values_list('user_id', flat=True)
            self.fields['invited_user'].queryset = User.objects.filter(
                user_type='student'
            ).exclude(id__in=team_members)
    
    def clean_invited_user(self):
        """Validate invited user"""
        invited_user = self.cleaned_data.get('invited_user')
        
        if self.team and self.team.members.filter(user=invited_user).exists():
            raise ValidationError('This user is already a member of this team.')
        
        if self.team and self.team.invitations.filter(
            invited_user=invited_user,
            status='pending'
        ).exists():
            raise ValidationError('This user already has a pending invitation.')
        
        return invited_user


class ManageJoinRequestForm(forms.Form):
    """Form for managing join requests (accept/reject)"""
    STATUS_CHOICES = [
        ('accepted', 'Accept Request'),
        ('rejected', 'Reject Request'),
    ]
    
    status = forms.ChoiceField(choices=STATUS_CHOICES, widget=forms.RadioSelect())
    response_message = forms.CharField(
        required=False,
        label='Response Message (for rejection)',
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Provide reason for rejection (optional)',
            'rows': 3
        })
    )


class SelectStudentToInviteForm(forms.Form):
    """Form to search and select student to invite"""
    student = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type='student'),
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label='Select Student'
    )
    
    def __init__(self, *args, team=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.team = team
        
        if team:
            team_members = team.members.values_list('user_id', flat=True)
            self.fields['student'].queryset = User.objects.filter(
                user_type='student'
            ).exclude(id__in=team_members)
