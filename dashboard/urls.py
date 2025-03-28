# dashboard/urls.py

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_home, name='home'),
    path('public-notes/', views.manage_public_notes, name='manage_public_notes'),
    path('public-notes/<int:notebook_id>/toggle-featured/', views.toggle_featured, name='toggle_featured'),
    path('public-notes/<int:notebook_id>/unpublish/', views.unpublish_note, name='unpublish_note'),
    path('users/', views.manage_users, name='manage_users'),
]