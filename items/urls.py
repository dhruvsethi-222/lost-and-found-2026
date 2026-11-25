"""Web addresses for items, all starting with /items/."""
from django.urls import path

from . import views

app_name = 'items'

urlpatterns = [
    path('report/', views.report_item, name='report'),
    path('report/<int:pk>/photo/', views.report_photo, name='report_photo'),
    path('desk/found/new/', views.record_found_item, name='desk_record_found'),
    path('desk/found/', views.found_item_list, name='desk_found_list'),
    path('desk/found/<int:pk>/', views.found_item_detail, name='desk_found_detail'),
    path('desk/reports/', views.report_list, name='desk_reports'),
    path('desk/matches/', views.match_list, name='desk_matches'),
    path('desk/expired/', views.expired_list, name='desk_expired'),
    path('desk/found/<int:pk>/dispose/', views.dispose_item, name='desk_dispose'),
]
