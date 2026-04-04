"""
Admin configuration for Event models
"""

from django.contrib import admin
from accounts.models import Event, Registration, Team, TeamMember, Payment, Notification


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'organizer', 'event_type', 'category', 'date', 'status', 'seats', 'available_seats', 'is_paid']
    list_filter = ['event_type', 'category', 'status', 'is_paid', 'date']
    search_fields = ['title', 'description', 'organizer__username']
    ordering = ['-date']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'organizer', 'event_type', 'category')
        }),
        ('Date & Location', {
            'fields': ('date', 'deadline', 'location')
        }),
        ('Capacity & Pricing', {
            'fields': ('seats', 'available_seats', 'is_paid', 'price')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'status', 'registered_at', 'updated_at']
    list_filter = ['status', 'registered_at', 'event__event_type']
    search_fields = ['user__username', 'event__title']
    ordering = ['-registered_at']
    readonly_fields = ['registered_at', 'updated_at']

    fieldsets = (
        ('Registration Details', {
            'fields': ('user', 'event', 'status')
        }),
        ('Cancellation', {
            'fields': ('cancellation_reason',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('registered_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['team_name', 'event', 'team_lead', 'max_members', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'event__event_type']
    search_fields = ['team_name', 'team_lead__username', 'event__title']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['user', 'team', 'role', 'joined_at']
    list_filter = ['role', 'joined_at', 'team__event__event_type']
    search_fields = ['user__username', 'team__team_name']
    ordering = ['-joined_at']
    readonly_fields = ['joined_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['user', 'event', 'total_amount', 'status', 'payment_method', 'created_at']
    list_filter = ['status', 'payment_method', 'created_at']
    search_fields = ['user__username', 'event__title', 'transaction_id']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Payment Details', {
            'fields': ('user', 'event', 'total_amount', 'platform_fee', 'organizer_amount')
        }),
        ('Payment Status', {
            'fields': ('status', 'payment_method', 'transaction_id')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'notification_type', 'is_sent', 'sent_at', 'created_at']
    list_filter = ['notification_type', 'is_sent', 'created_at']
    search_fields = ['user__username', 'message']
    ordering = ['-created_at']
    readonly_fields = ['sent_at', 'created_at', 'updated_at']

    fieldsets = (
        ('Notification Details', {
            'fields': ('user', 'event', 'notification_type', 'message')
        }),
        ('Delivery Status', {
            'fields': ('is_sent', 'sent_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )