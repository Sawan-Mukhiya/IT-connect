from django.contrib import admin
from .models import (
    User, AdminProfile, OrganizerProfile, StudentProfile, StudentInterest,
    StudentSkill, StudentAchievement,
    Team, TeamMember, TeamJoinRequest, TeamInvitation
)


# ============================================================================
# USER & PROFILE ADMINS
# ============================================================================

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'user_type', 'is_superuser', 'created_at')
    list_filter = ('user_type', 'is_superuser', 'created_at')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('username', 'email', 'first_name', 'last_name', 'phone_number')
        }),
        ('Profile', {
            'fields': ('user_type', 'profile_picture')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'department')
    search_fields = ('user__username', 'employee_id', 'department')
    readonly_fields = ('user',)


@admin.register(OrganizerProfile)
class OrganizerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization_name', 'organization_type')
    list_filter = ('organization_type',)
    search_fields = ('user__username', 'organization_name')
    readonly_fields = ('user',)


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_id', 'grade_level', 'graduation_year')
    list_filter = ('graduation_year', 'grade_level')
    search_fields = ('user__username', 'student_id')
    readonly_fields = ('user', 'event_enroll_count')


@admin.register(StudentInterest)
class StudentInterestAdmin(admin.ModelAdmin):
    list_display = ('student', 'interest', 'created_at')
    list_filter = ('interest',)
    search_fields = ('student__username',)
    readonly_fields = ('created_at',)


@admin.register(StudentSkill)
class StudentSkillAdmin(admin.ModelAdmin):
    list_display = ('student', 'skill', 'level', 'added_at')
    list_filter = ('level', 'skill')
    search_fields = ('student__username', 'skill')
    readonly_fields = ('added_at',)


@admin.register(StudentAchievement)
class StudentAchievementAdmin(admin.ModelAdmin):
    list_display = ('student', 'title', 'achievement_type', 'earned_at', 'event')
    list_filter = ('achievement_type', 'earned_at')
    search_fields = ('student__username', 'title')
    readonly_fields = ('earned_at',)


# ============================================================================
# TEAM ADMINS
# ============================================================================

class TeamMemberInline(admin.TabularInline):
    """Inline admin for team members"""
    model = TeamMember
    extra = 1
    fields = ('user', 'role', 'joined_at')
    readonly_fields = ('joined_at',)


class TeamJoinRequestInline(admin.TabularInline):
    """Inline admin for join requests"""
    model = TeamJoinRequest
    extra = 0
    fields = ('user', 'status', 'message', 'requested_at')
    readonly_fields = ('requested_at',)
    can_delete = False


class TeamInvitationInline(admin.TabularInline):
    """Inline admin for invitations"""
    model = TeamInvitation
    extra = 0
    fields = ('invited_user', 'status', 'created_at')
    readonly_fields = ('created_at',)
    can_delete = False


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('team_name', 'event', 'team_lead', 'member_count', 'max_members', 'visibility', 'status')
    list_filter = ('visibility', 'status', 'created_at', 'event')
    search_fields = ('team_name', 'team_lead__username', 'event__title')
    readonly_fields = ('created_at', 'updated_at', 'team_code')
    inlines = [TeamMemberInline, TeamJoinRequestInline, TeamInvitationInline]
    
    fieldsets = (
        ('Team Information', {
            'fields': ('team_name', 'description', 'event')
        }),
        ('Leadership & Size', {
            'fields': ('team_lead', 'max_members')
        }),
        ('Settings', {
            'fields': ('visibility', 'team_code')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def member_count(self, obj):
        """Display current member count"""
        return f"{obj.get_current_member_count()}/{obj.max_members}"
    member_count.short_description = 'Members'


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'role', 'joined_at')
    list_filter = ('role', 'joined_at')
    search_fields = ('user__username', 'team__team_name')
    readonly_fields = ('joined_at',)


@admin.register(TeamJoinRequest)
class TeamJoinRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'status', 'requested_at')
    list_filter = ('status', 'requested_at')
    search_fields = ('user__username', 'team__team_name')
    readonly_fields = ('requested_at', 'responded_at')
    
    fieldsets = (
        ('Request Information', {
            'fields': ('team', 'user', 'message')
        }),
        ('Status', {
            'fields': ('status', 'response_message')
        }),
        ('Timestamps', {
            'fields': ('requested_at', 'responded_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TeamInvitation)
class TeamInvitationAdmin(admin.ModelAdmin):
    list_display = ('invited_user', 'team', 'invited_by', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('invited_user__username', 'team__team_name')
    readonly_fields = ('created_at', 'responded_at')
    
    fieldsets = (
        ('Invitation Information', {
            'fields': ('team', 'invited_user', 'invited_by', 'message')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timing', {
            'fields': ('created_at', 'responded_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )
