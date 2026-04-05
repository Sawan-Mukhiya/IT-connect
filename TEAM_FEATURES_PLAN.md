# Team Management Feature Plan - IT Connect

## Overview
A comprehensive team management system allowing students to form teams, invite others, manage membership requests, and participate in events as teams.

---

## Core Features to Build

### 1. Team Creation & Management
- ✅ **Create Team**
  - Student initiates team creation
  - Set team name, description, max members
  - Select event(s) for team
  - Set team visibility (public/private)
  - Team leader = creator

- ✅ **Team Settings**
  - Edit team name, description, max members
  - Change visibility
  - Set team logo/image
  - Team code (for easy joining)
  - Leave team (if not leader)

- ✅ **Disband/Delete Team**
  - Leader can disband team
  - Requires confirmation
  - Archive team history

---

### 2. Team Membership Management

#### A. **Join Operations**
- ✅ **Direct Join** (Public Teams)
  - View public teams
  - Click "Join Team" button
  - Instant join if slots available
  - Get added to members list

- ✅ **Request to Join** (Private Teams)
  - Click "Request to Join"
  - Add optional request message
  - Sends notification to leader
  - Pending status until accepted

- ✅ **Team Code Join**
  - Use team code to join
  - Bypasses discovery need
  - Can be shared via invite link
  - Works for both public and private teams

#### B. **Invitations**
- ✅ **Send Team Invitation**
  - Leader/members invite students
  - Search students by username/email
  - Send invitation with message
  - Recipient gets notification

- ✅ **Accept/Reject Invitation**
  - View pending invitations
  - Accept → Join team
  - Reject → Decline invitation
  - Invitation expires after 7 days

- ✅ **Cancel Invitation**
  - Leader/sender can cancel sent invitation
  - Recipient no longer sees it

---

### 3. Request Management

#### A. **Join Requests**
- ✅ **View Pending Requests**
  - Leader sees list of join requests
  - Shows applicant info
  - Shows request message
  - Shows application date

- ✅ **Accept Request**
  - Leader approves request
  - Student added to team
  - Notification sent to student
  - Check max members limit

- ✅ **Reject Request**
  - Leader rejects request
  - Optional rejection reason
  - Notification sent to student
  - Student can request again later

- ✅ **Withdraw Request**
  - Student can withdraw pending request
  - No longer waiting for response
  - Can request again later

---

### 4. Team Roles & Permissions

- **Team Leader**
  - Create team
  - Edit team settings
  - Accept/reject join requests
  - Invite members
  - Remove members
  - Dissolve team
  - Register team for events

- **Team Member**
  - View team info
  - See team members
  - Leave team
  - View team registrations
  - (Optional) Send invitations

- **Administrator**
  - Moderate teams
  - Remove problematic teams
  - View all teams
  - Support user issues

---

### 5. Team Dashboard (New Page)

- ✅ **Team Overview**
  - Team name, description, logo
  - Current members count / max
  - Team creation date
  - Event(s) registered for
  - Team status (active/archived)

- ✅ **Members Section**
  - List all members
  - Show member roles
  - Show join dates
  - Remove member button (leader only)
  - Promote/demote member (future)

- ✅ **Join Requests Section**
  - Pending requests list
  - Accept/Reject buttons
  - Request message visible
  - Date requested

- ✅ **Invitations Section**
  - Sent invitations
  - Pending invitations
  - Cancel button
  - Acceptance status

- ✅ **Team Actions**
  - Edit team settings
  - Copy team code
  - Share team link
  - Leave team
  - Disband team (leader only)
  - Register team for event (leader only)

---

### 6. Team Discovery & Search

- ✅ **Browse Teams Page**
  - List all public teams
  - Filter by event
  - Filter by member count
  - Search by team name
  - Sort by recent, popular, most members

- ✅ **Team Detail Page**
  - Team info and description
  - Members count and list (preview)
  - Events registered for
  - "Join" or "Request to Join" button
  - Copy team code button

- ✅ **My Teams Page**
  - Teams user is member of
  - Teams user owns
  - Teams with pending requests (leading)
  - Teams with pending invitations (member)

---

### 7. Notifications & Events

- ✅ **Notifications Generated**
  - User receives join request
  - User receives invitation
  - Join request accepted/rejected
  - Invitation accepted/rejected
  - Member left team
  - Member removed by leader
  - Team disbanded
  - User invited to join event

- ✅ **Notification Features**
  - In-app notifications
  - Quick action buttons
  - Mark as read
  - Delete notification
  - (Future) Email notifications

---

### 8. Event Integration

- ✅ **Register Team for Event**
  - Leader registers team for event
  - Team counted as one registration
  - All members included
  - Event shows team info

- ✅ **Team Participation**
  - View events team is registered for
  - View team's performance/results
  - Team dashboard shows registrations

---

### 9. Constraints & Validation

- ✅ **Team Size Limits**
  - Min members: 2 (or 1?)
  - Max members: Customizable (2-5, 5-10, etc.)
  - Set during team creation
  - Prevent join if full

- ✅ **Team Name Rules**
  - Unique team name per event
  - Min 3 characters
  - Max 50 characters
  - No special characters
  - Profanity filter

- ✅ **Membership Rules**
  - One student can be in multiple teams
  - (Optional) Limit: 1 team per event
  - (Optional) Limit: 3 teams max per student
  - Cannot be in team with same person twice

- ✅ **Request/Invitation Limits**
  - Team code expires after X days
  - Invite expires after 7 days
  - Limit pending invites per team
  - Prevent duplicate requests

---

### 10. Admin Moderation

- ✅ **Team Moderation**
  - View all teams
  - Search teams
  - Delete inappropriate teams
  - View team members
  - Handle abuse reports
  - Suspend team (future)

- ✅ **Member Reporting**
  - Report inappropriate member
  - Report inappropriate team
  - View reports in admin panel

---

## Database Models to Create

```python
# Team Model
class Team(models.Model):
    name = CharField(max_length=50)
    description = TextField()
    leader = ForeignKey(User)
    created_at = DateTimeField()
    max_members = IntegerField()
    visibility = CharField(choices=[public, private])
    logo = ImageField()
    team_code = CharField(unique=True)
    is_active = BooleanField()
    created_event = ForeignKey(Event, null=True)
    
# TeamMember Model
class TeamMember(models.Model):
    team = ForeignKey(Team)
    user = ForeignKey(User)
    joined_at = DateTimeField()
    role = CharField(choices=[leader, member])
    
# TeamJoinRequest Model
class TeamJoinRequest(models.Model):
    team = ForeignKey(Team)
    user = ForeignKey(User)
    message = TextField()
    status = CharField(choices=[pending, accepted, rejected])
    requested_at = DateTimeField()
    responded_at = DateTimeField()
    response_message = TextField()
    
# TeamInvitation Model
class TeamInvitation(models.Model):
    team = ForeignKey(Team)
    invited_user = ForeignKey(User)
    invited_by = ForeignKey(User)
    message = TextField()
    status = CharField(choices=[pending, accepted, rejected])
    created_at = DateTimeField()
    responded_at = DateTimeField()
    expires_at = DateTimeField()
    
# TeamEvent Registration (if teams can register for events)
class TeamEventRegistration(models.Model):
    team = ForeignKey(Team)
    event = ForeignKey(Event)
    registered_at = DateTimeField()
    status = CharField(choices=[registered, completed, withdrawn])
```

---

## Pages/Views to Create

1. **Team Management**
   - `/teams/` - Team discovery/browse page
   - `/teams/my-teams/` - My teams page
   - `/teams/create/` - Create team form
   - `/teams/<id>/` - Team detail page
   - `/teams/<id>/dashboard/` - Team dashboard (edit, manage, etc)
   - `/teams/<id>/members/` - Team members list

2. **Team Actions**
   - `/teams/<id>/edit/` - Edit team settings
   - `/teams/<id>/join/` - Join team action
   - `/teams/<id>/request-join/` - Request to join action
   - `/teams/<id>/invite/` - Invite member form
   - `/teams/<id>/leave/` - Leave team action
   - `/teams/<id>/disband/` - Disband team action

3. **Notifications**
   - `/notifications/` - All notifications
   - `/notifications/team/` - Team-related notifications

---

## Suggested Implementation Strategy

### Phase 1 (MVP - Core Features)
1. Create Team models
2. Create team dashboard and management
3. Implement direct join for public teams
4. Implement Team CRUD operations
5. Create team list/discovery page

### Phase 2 (Requests & Invitations)
6. Implement join requests for private teams
7. Implement team invitations
8. Add request/invitation management UI
9. Accept/reject functionality

### Phase 3 (Advanced)
10. Team code generation
11. Event registration as team
12. Notifications system
13. Admin moderation tools
14. Team search and filtering

### Phase 4 (Polish)
15. Team roles and permissions
16. Analytics and statistics
17. Archive old teams
18. Export team data

---

## Additional Features (Nice to Have)

- ✅ Team chat/messaging
- ✅ Team achievements/badges
- ✅ Team statistics and analytics
- ✅ Team event history
- ✅ Recommendation: "Add X as teammate" based on interests
- ✅ Team sponsorship/funding info
- ✅ Team skill tags
- ✅ Team reputation score
- ✅ Leaderboards (teams)
- ✅ Team profile customization
- ✅ Team social links

---

## Questions to Clarify

1. **Membership Limits**
   - Can one student be in multiple teams?
   - Can one student be in multiple teams for the same event?
   - What's typical team size? (2-5, 5-10?)

2. **Approval Process**
   - Should joining a public team be instant or require approval?
   - Should team leader approve all members?

3. **Event Binding**
   - Can a team exist without being tied to an event?
   - Can a team register for multiple events?

4. **Visibility**
   - Should teams have visibility/privacy settings?
   - Can anyone view team members?

5. **Roles**
   - Should we have sub-roles like co-leader, manager?
   - What permissions do members have?

6. **Team Code**
   - Should we generate shareable invite codes?
   - Should codes expire?

---

## Success Criteria

- ✅ Students can create and manage teams
- ✅ Easy discovery and joining of teams
- ✅ Clear request/invitation workflows
- ✅ Notifications for all team activities
- ✅ Team dashboard with all operations
- ✅ Proper validation and constraints
- ✅ 100% test coverage for team features
- ✅ Responsive UI for all team pages

