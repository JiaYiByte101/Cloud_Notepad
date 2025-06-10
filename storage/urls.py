# storage/urls.py

from django.urls import path
from . import views

app_name = 'storage'

urlpatterns = [
    path('', views.storage_home, name='home'),
    
    # 云版本备份相关路由
    path('cloud-backup/', views.create_cloud_backup, name='create_cloud_backup'),
    path('cloud-backup/<int:backup_id>/download/', views.download_cloud_backup, name='download_cloud_backup'),
    path('cloud-backup/<int:backup_id>/delete/', views.delete_cloud_backup, name='delete_cloud_backup'),
    path('cloud-backup/<int:backup_id>/restore/', views.restore_cloud_backup, name='restore_cloud_backup'),
]