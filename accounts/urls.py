"""
Web addresses for accounts, all starting with /accounts/.

Log in and log out use Django's ready-made LoginView and LogoutView. We only tell
them which page (template) and which form to use.
"""
from django.contrib.auth.views import LoginView, LogoutView
from django.urls import path

from . import views
from .forms import CampusLoginForm, DeskLoginForm

app_name = 'accounts'

urlpatterns = [
    # Sign up: the same view, told which kind of account to make
    path('register/', views.register, {'role': 'student'}, name='register'),
    path('register/staff/', views.register, {'role': 'staff'}, name='register_staff'),

    # Email verification
    path('verification-sent/', views.verification_sent, name='verification_sent'),
    path('verify/<uidb64>/<token>/', views.verify_email, name='verify'),
    path('resend-verification/', views.resend_verification, name='resend'),

    # Log in for Students and Staff (ST-P2, SF-P2)
    path('login/', LoginView.as_view(template_name='accounts/login.html',
                                     authentication_form=CampusLoginForm,
                                     redirect_authenticated_user=True), name='login'),

    # Separate log in for the Admin (AD-P1)
    path('desk-login/', LoginView.as_view(template_name='accounts/desk_login.html',
                                          authentication_form=DeskLoginForm,
                                          redirect_authenticated_user=True), name='desk_login'),

    # Log out works only from the Log out button (a POST), never from a link
    path('logout/', LogoutView.as_view(), name='logout'),
]
