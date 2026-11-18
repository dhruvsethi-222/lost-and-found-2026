"""Web addresses for posts, all starting with /posts/."""
from django.urls import path

from . import views

app_name = 'posts'

urlpatterns = [
    path('', views.post_list, name='list'),
    path('<int:post_id>/reply/', views.reply, name='reply'),
]
