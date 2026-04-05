"""
Admin configuration for Event models
"""

from django.contrib import admin
from accounts.models import Event, Registration, Payment


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