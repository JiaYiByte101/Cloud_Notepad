# sharing/urls.py

from django.urls import path
from . import views

app_name = 'sharing'

urlpatterns = [
    path('public/', views.public_notes, name='public'),
    path('note/<int:notebook_id>/', views.view_shared_note, name='view_note'),
    path('note/<int:notebook_id>/like/', views.toggle_like, name='toggle_like'),
    path('comment/<int:comment_id>/like/', views.toggle_comment_like, name='toggle_comment_like'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
]