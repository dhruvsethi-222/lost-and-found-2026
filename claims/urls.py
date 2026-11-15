"""Web addresses for claims, all starting with /claims/."""
from django.urls import path

from . import views

app_name = 'claims'

urlpatterns = [
    # Student and Staff
    path('new/<int:found_item_id>/', views.submit_claim, name='new'),
    path('<int:claim_id>/add-details/', views.add_details, name='add_details'),

    # Admin
    path('desk/', views.claim_list, name='desk_list'),
    path('desk/<int:claim_id>/', views.verify_claim, name='desk_verify'),
]
