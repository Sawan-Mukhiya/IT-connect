"""
IT Connect - Updated Django Models
Implements the improved database schema with all suggestions
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


# ============================================================================
# USER & PROFILE MODELS (Consolidated)
# ============================================================================

class User(AbstractUser):
    """Consolidated user model for all account types (Student/Organizer/Admin)"""
    USER_TYPE_CHOICES = (
        ('admin', 'Admin'),
        ('organizer', 'Organizer'),
        ('student', 'Student'),
    )
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='student')
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['user_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"


class AdminProfile(models.Model):
    """Profile extension for admin users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    department = models.CharField(max_length=100)
    employee_id = models.CharField(max_length=50, unique=True)
    permissions = models.TextField(help_text="JSON string of permissions")

    def __str__(self):
        return f"Admin: {self.user.username}"


class OrganizerProfile(models.Model):
    """Profile extension for organizer users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='organizer_profile')
    organization_name = models.CharField(max_length=200)
    organization_type = models.CharField(max_length=100)
    license_number = models.CharField(max_length=100, blank=True, null=True)
    license_image = models.ImageField(upload_to='license_images/', blank=True, null=True)
    website = models.URLField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['organization_type']),
        ]

    def __str__(self):
        return f"Organizer: {self.user.username}"


class StudentProfile(models.Model):
    """Profile extension for student users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=50, unique=True)
    grade_level = models.CharField(max_length=50)
    major = models.CharField(max_length=100, blank=True, null=True)
    graduation_year = models.IntegerField()
    gpa = models.DecimalField(max_digits=3, decimal_places=2, blank=True, null=True, 
                             validators=[MinValueValidator(0.0), MaxValueValidator(4.0)])
    event_enroll_count = models.IntegerField(default=0)  # Track total enrollments

    class Meta:
        indexes = [
            models.Index(fields=['student_id']),
            models.Index(fields=['graduation_year']),
        ]

    def __str__(self):
        return f"Student: {self.user.username}"


# ============================================================================
# STUDENT INTERESTS (For Recommendations)
# ============================================================================

class StudentInterest(models.Model):
    """Track student interests for recommendation engine"""
    INTEREST_CHOICES = (
        ('seminar', 'Seminar'),
        ('workshop', 'Workshop'),
        ('hackathon', 'Hackathon'),
        ('ai_ml', 'AI & Machine Learning'),
        ('web_dev', 'Web Development'),
        ('mobile_dev', 'Mobile Development'),
        ('data_science', 'Data Science'),
        ('cloud', 'Cloud & DevOps'),
        ('cybersecurity', 'Cybersecurity'),
        ('iot', 'IoT'),
        ('blockchain', 'Blockchain'),
        ('other', 'Other'),
    )
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interests')
    interest = models.CharField(max_length=50, choices=INTEREST_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'interest')
        indexes = [
            models.Index(fields=['student', 'interest']),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.get_interest_display()}"


# ============================================================================
# STUDENT SKILLS
# ============================================================================

class StudentSkill(models.Model):
    """Track student technical and soft skills"""
    SKILL_LEVEL_CHOICES = (
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    )

    SKILL_CHOICES = (
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('java', 'Java'),
        ('csharp', 'C#'),
        ('cpp', 'C++'),
        ('react', 'React'),
        ('nodejs', 'Node.js'),
        ('django', 'Django'),
        ('sql', 'SQL'),
        ('mongodb', 'MongoDB'),
        ('docker', 'Docker'),
        ('kubernetes', 'Kubernetes'),
        ('aws', 'Amazon AWS'),
        ('azure', 'Microsoft Azure'),
        ('gcp', 'Google Cloud'),
        ('git', 'Git'),
        ('agile', 'Agile'),
        ('problem_solving', 'Problem Solving'),
        ('communication', 'Communication'),
        ('teamwork', 'Teamwork'),
        ('leadership', 'Leadership'),
        ('project_management', 'Project Management'),
        ('other', 'Other'),
    )

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skills')
    skill = models.CharField(max_length=50, choices=SKILL_CHOICES)
    level = models.CharField(max_length=20, choices=SKILL_LEVEL_CHOICES, default='beginner')
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'skill')
        indexes = [
            models.Index(fields=['student', 'level']),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.get_skill_display()} ({self.get_level_display()})"


# ============================================================================
# STUDENT ACHIEVEMENTS & BADGES
# ============================================================================

class StudentAchievement(models.Model):
    """Track student achievements, badges, and certifications"""
    ACHIEVEMENT_TYPE_CHOICES = (
        ('badge', 'Badge'),
        ('certificate', 'Certificate'),
        ('award', 'Award'),
        ('participation', 'Participation'),
    )

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    achievement_type = models.CharField(max_length=20, choices=ACHIEVEMENT_TYPE_CHOICES, default='badge')
    icon = models.CharField(max_length=100, blank=True, help_text="Font Awesome icon name, e.g., trophy, star")
    earned_at = models.DateTimeField(auto_now_add=True)
    event = models.ForeignKey('Event', on_delete=models.SET_NULL, null=True, blank=True,
                             related_name='student_achievements')
    
    class Meta:
        ordering = ['-earned_at']
        indexes = [
            models.Index(fields=['student', 'achievement_type']),
            models.Index(fields=['earned_at']),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.title}"


# ============================================================================
# EVENT MODEL
# ============================================================================

class Event(models.Model):
    """Main Events table"""
    EVENT_TYPE_CHOICES = (
        ('seminar', 'Seminar'),
        ('workshop', 'Workshop'),
        ('hackathon', 'Hackathon'),
    )
    
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    )
    
    CATEGORY_CHOICES = (
        ('tech', 'Technology'),
        ('ai_ml', 'AI & Machine Learning'),
        ('web', 'Web Development'),
        ('mobile', 'Mobile Development'),
        ('data', 'Data Science'),
        ('cloud', 'Cloud & DevOps'),
        ('security', 'Cybersecurity'),
        ('iot', 'IoT'),
        ('blockchain', 'Blockchain'),
        ('other', 'Other'),
    )

    title = models.CharField(max_length=500)
    description = models.TextField()
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events',
                                 limit_choices_to={'user_type': 'organizer'})
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    date = models.DateTimeField()
    deadline = models.DateTimeField()  # Registration deadline
    location = models.CharField(max_length=500, blank=True, null=True)  # Physical location or virtual
    
    seats = models.IntegerField(validators=[MinValueValidator(1)])
    available_seats = models.IntegerField()  # Auto-update based on registrations
    
    is_paid = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, 
                               validators=[MinValueValidator(0)])
    
    image = models.ImageField(upload_to='event_posters/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    is_approved = models.BooleanField(default=False, help_text="Event must be approved by admin to be visible")
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, 
                                    related_name='approved_events', limit_choices_to={'user_type': 'admin'})
    approved_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['organizer', 'status']),
            models.Index(fields=['event_type']),
            models.Index(fields=['category']),
            models.Index(fields=['date']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.title} by {self.organizer.username}"

    def save(self, *args, **kwargs):
        """Auto-update available_seats on save"""
        if self.id:
            registered_count = self.registrations.filter(status='registered').count()
            self.available_seats = self.seats - registered_count
        else:
            self.available_seats = self.seats
        super().save(*args, **kwargs)


# ============================================================================
# REGISTRATION MODEL (Replaces old Enrollment)
# ============================================================================

class Registration(models.Model):
    """User registration for events"""
    STATUS_CHOICES = (
        ('registered', 'Registered'),
        ('cancelled', 'Cancelled'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='registrations')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='registered')
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancellation_reason = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('user', 'event')
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['event', 'status']),
            models.Index(fields=['registered_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.event.title} ({self.status})"


# ============================================================================
# TEAM MODELS (Only for Hackathons)
# ============================================================================

class Team(models.Model):
    """Teams for hackathon events"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
    )
    
    VISIBILITY_CHOICES = (
        ('public', 'Public'),
        ('private', 'Private'),
    )

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='teams',
                             limit_choices_to={'event_type': 'hackathon'})
    team_name = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True, help_text="Team description and goals")
    team_lead = models.ForeignKey(User, on_delete=models.CASCADE, related_name='led_teams')
    max_members = models.IntegerField(validators=[MinValueValidator(2)], default=4)
    team_code = models.CharField(max_length=12, unique=True, blank=True, null=True, help_text="Unique code for joining team")
    visibility = models.CharField(max_length=20, choices=VISIBILITY_CHOICES, default='public')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('event', 'team_name')
        indexes = [
            models.Index(fields=['event', 'status']),
            models.Index(fields=['team_lead']),
            models.Index(fields=['team_code']),
            models.Index(fields=['visibility']),
        ]

    def __str__(self):
        return f"{self.team_name} - {self.event.title}"
    
    def get_current_member_count(self):
        """Get current number of members in team"""
        return self.members.count()
    
    def is_full(self):
        """Check if team is full"""
        return self.get_current_member_count() >= self.max_members

    def spots_remaining(self):
        return max(0, self.max_members - self.get_current_member_count())


class TeamMember(models.Model):
    """Junction table for Team ↔ User many-to-many relationship"""
    ROLE_CHOICES = (
        ('member', 'Member'),
        ('leader', 'Leader'),
    )

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('team', 'user')
        indexes = [
            models.Index(fields=['team', 'role']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username} in {self.team.team_name} ({self.get_role_display()})"


class TeamJoinRequest(models.Model):
    """Request to join a team"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    )
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='join_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_join_requests')
    message = models.TextField(blank=True, null=True, help_text="Why do you want to join this team?")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)
    response_message = models.TextField(blank=True, null=True, help_text="Rejection reason if rejected")
    
    class Meta:
        unique_together = ('team', 'user')
        indexes = [
            models.Index(fields=['team', 'status']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} join request for {self.team.team_name} ({self.status})"


class TeamInvitation(models.Model):
    """Invitation to join a team"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )
    
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='invitations')
    invited_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_invitations')
    invited_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_team_invitations')
    message = models.TextField(blank=True, null=True, help_text="Invitation message")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)
    expires_at = models.DateTimeField(help_text="Invitation expires after 7 days")
    
    class Meta:
        unique_together = ('team', 'invited_user')
        indexes = [
            models.Index(fields=['team', 'status']),
            models.Index(fields=['invited_user', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.invited_user.username} invited to {self.team.team_name} ({self.status})"


# ============================================================================
# PAYMENT MODEL
# ============================================================================

class Payment(models.Model):
    """Tracks payments for paid events"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    )

    PAYMENT_METHOD_CHOICES = (
        ('card', 'Credit/Debit Card'),
        ('upi', 'UPI'),
        ('net_banking', 'Net Banking'),
        ('wallet', 'Digital Wallet'),
        ('simulation', 'Simulated Payment'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payments')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='payments')
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    organizer_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_method = models.CharField(max_length=50, choices=PAYMENT_METHOD_CHOICES, default='simulation')
    transaction_id = models.CharField(max_length=200, blank=True, null=True, unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['event']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"Payment - {self.user.username} for {self.event.title} ({self.status})"


# ============================================================================
# NOTIFICATION MODEL (For Email Tracking)
# ============================================================================

class Notification(models.Model):
    """Track all notifications sent to users"""
    NOTIFICATION_TYPE_CHOICES = (
        ('event_registered', 'Event Registered'),
        ('event_cancelled', 'Event Cancelled'),
        ('registration_cancelled', 'Registration Cancelled'),
        ('payment_confirmed', 'Payment Confirmed'),
        ('payment_failed', 'Payment Failed'),
        ('team_join_request', 'Team Join Request'),
        ('team_join_request_accepted', 'Team Join Request Accepted'),
        ('team_join_request_rejected', 'Team Join Request Rejected'),
        ('team_invitation', 'Team Invitation'),
        ('team_invitation_accepted', 'Team Invitation Accepted'),
        ('team_invitation_rejected', 'Team Invitation Rejected'),
        ('team_member_joined', 'Team Member Joined'),
        ('team_member_left', 'Team Member Left'),
        ('event_reminder', 'Event Reminder'),
        ('promotion', 'Promotion'),
        ('recommendation', 'Event Recommendation'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='notifications', 
                             blank=True, null=True)
    
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPE_CHOICES)
    message = models.TextField()
    
    is_sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['user', 'is_sent']),
            models.Index(fields=['notification_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.get_notification_type_display()}"


# ============================================================================
# ANALYTICS MODELS
# ============================================================================

class OrganizerAnalytics(models.Model):
    """Track analytics for organizers"""
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics',
                                 limit_choices_to={'user_type': 'organizer'})
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='analytics')
    
    total_registrations = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    team_count = models.IntegerField(default=0)  # Only for hackathons
    
    updated_at = models.DateTimeField(auto_now=True)
    calculated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('organizer', 'event')
        indexes = [
            models.Index(fields=['organizer']),
        ]

    def __str__(self):
        return f"Analytics - {self.organizer.username} for {self.event.title}"


class StudentRecommendation(models.Model):
    """Track recommended events for students (rule-based recommendation engine)"""
    REASON_CHOICES = (
        ('category_match', 'Category Match'),
        ('interest_match', 'Interest Match'),
        ('friend_attending', 'Friend Attending'),
        ('trending', 'Trending Event'),
        ('organizer_follow', 'Following Organizer'),
    )

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations',
                               limit_choices_to={'user_type': 'student'})
    recommended_event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='student_recommendations')
    reason = models.CharField(max_length=50, choices=REASON_CHOICES)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'recommended_event')
        indexes = [
            models.Index(fields=['student', 'created_at']),
        ]

    def __str__(self):
        return f"Recommended {self.recommended_event.title} to {self.student.username} ({self.get_reason_display()})"
