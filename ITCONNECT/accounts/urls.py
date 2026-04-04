from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='home'),
    path('about/', views.about_page, name='about'),
    path('contact/', views.contact_page, name='contact'),
    path('choose-type/', views.choose_registration_type, name='choose_registration_type'),
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('success/', views.registration_success, name='registration_success'),
]
