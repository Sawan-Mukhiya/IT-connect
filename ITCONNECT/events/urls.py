"""
URL patterns for Event Management
"""

from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    # Public event views
    path('', views.event_list, name='event_list'),
    path('<int:event_id>/', views.event_detail, name='event_detail'),
    path('<int:event_id>/register/', views.event_register, name='event_register'),
    path('<int:event_id>/unregister/', views.event_unregister, name='event_unregister'),

    # Organizer views
    path('organizer/dashboard/', views.organizer_dashboard, name='organizer_dashboard'),
    path('organizer/create/', views.create_event, name='create_event'),
    path('organizer/<int:event_id>/edit/', views.edit_event, name='edit_event'),

    # Student views
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/generate-recommendations/', views.generate_recommendations, name='generate_recommendations'),
]