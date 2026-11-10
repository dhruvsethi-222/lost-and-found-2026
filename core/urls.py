from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('start/', views.after_login, name='after_login'),
    path('my/', views.my_page, name='my_page'),
    path('desk/', views.desk, name='desk'),
]
