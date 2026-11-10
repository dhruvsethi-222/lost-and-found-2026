from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views
from .models import Role

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register, {'role': Role.STUDENT}, name='register'),
    path('register/staff/', views.register, {'role': Role.STAFF}, name='register_staff'),
    path('verification-sent/', views.verification_sent, name='verification_sent'),
    path('verify/<uidb64>/<token>/', views.verify_email, name='verify'),
    path('resend-verification/', views.resend_verification, name='resend'),
    path('login/', views.CampusLoginView.as_view(), name='login'),
    path('desk-login/', views.DeskLoginView.as_view(), name='desk_login'),
    path('logout/', LogoutView.as_view(), name='logout'),          # log out only by a button (POST)
]
