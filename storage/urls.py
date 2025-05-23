# storage/urls.py

from django.urls import path
from . import views

app_name = 'storage'

urlpatterns = [
    path('', views.storage_home, name='home'),
    path('backup/', views.backup, name='backup'),
    path('backup/<int:backup_id>/download/', views.download_backup, name='download_backup'),
    path('backup/<int:backup_id>/delete/', views.delete_backup, name='delete_backup'),
    path('backup/<int:backup_id>/restore/', views.restore_backup, name='restore_backup'),
    path('sync/status/', views.sync_status, name='sync_status'),
    path('sync/now/', views.sync_now, name='sync_now'),
    path('cloud/', views.cloud_storage, name='cloud_storage'),
    path('save-to-cloud/<int:notebook_id>/', views.save_to_cloud, name='save_to_cloud'),
    path('sync-cloud/', views.sync_cloud, name='sync_cloud'),
    path('delete-cloud-file/', views.delete_cloud_file, name='delete_cloud_file'),
]