from django.urls import path
from . import views

app_name = 'teams'

urlpatterns = [
    # Team Discovery & Listing
    path('', views.TeamsHomeView.as_view(), name='teams_home'),
    path('discover/', views.TeamListView.as_view(), name='team_list'),
    path('my-teams/', views.MyTeamsView.as_view(), name='my_teams'),
    path('<int:pk>/', views.TeamDetailView.as_view(), name='team_detail'),
    
    # Team Creation & Management
    path('create/', views.CreateTeamView.as_view(), name='create_team'),
    path('<int:pk>/edit/', views.EditTeamView.as_view(), name='edit_team'),
    path('<int:pk>/delete/', views.DeleteTeamView.as_view(), name='delete_team'),
    
    # Join Requests
    path('<int:team_id>/request-join/', views.RequestToJoinView.as_view(), name='request_join'),
    path('<int:team_id>/join-requests/', views.JoinRequestListView.as_view(), name='join_requests'),
    path('join-request/<int:request_id>/accept/', views.AcceptJoinRequestView.as_view(), name='accept_join_request'),
    path('join-request/<int:request_id>/reject/', views.RejectJoinRequestView.as_view(), name='reject_join_request'),
    
    # Invitations
    path('<int:team_id>/invite/', views.InviteMemberView.as_view(), name='invite_member'),
    path('invitation/<int:invitation_id>/accept/', views.AcceptInvitationView.as_view(), name='accept_invitation'),
    path('invitation/<int:invitation_id>/reject/', views.RejectInvitationView.as_view(), name='reject_invitation'),
    
    # Member Management
    path('member/<int:member_id>/remove/', views.RemoveMemberView.as_view(), name='remove_member'),
    path('<int:team_id>/leave/', views.LeaveTeamView.as_view(), name='leave_team'),
]
