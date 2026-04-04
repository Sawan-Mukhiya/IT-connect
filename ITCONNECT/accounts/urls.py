from django.urls import path
from . import views

urlpatterns = [
    path('', views.choose_registration_type, name='home'),
    path('choose-type/', views.choose_registration_type, name='choose_registration_type'),
    path('register/', views.RegistrationView.as_view(), name='register'),
    path('success/', views.registration_success, name='registration_success'),
]
