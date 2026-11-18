"""Web addresses for the hand-over, all starting with /handover/."""
from django.urls import path

from . import views

app_name = 'handover'

urlpatterns = [
    path('', views.hand_over_list, name='list'),
    path('<int:claim_id>/', views.record_hand_over, name='record'),
]
