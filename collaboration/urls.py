from django.urls import path
from . import views
from notebooks.views import notebook_download_pdf, notebook_download_html

app_name = 'collaboration'

urlpatterns = [
    # 项目管理
    path('projects/', views.project_list, name='project_list'),
    path('projects/create/', views.create_project, name='create_project'),
    path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
    path('projects/<int:project_id>/edit/', views.edit_project, name='edit_project'),
    path('projects/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    
    # 成员管理
    path('projects/<int:project_id>/invite/', views.invite_member, name='invite_member'),
    path('invitations/<int:member_id>/<str:action>/', views.handle_invitation, name='handle_invitation'),
    path('projects/<int:project_id>/members/<int:member_id>/remove/', views.remove_member, name='remove_member'),
    path('members/<int:member_id>/change-role/', views.change_member_role, name='change_member_role'),
    
    # 笔记锁定
    path('notebooks/<int:notebook_id>/lock/', views.lock_notebook, name='lock_notebook'),
    path('notebooks/<int:notebook_id>/release-lock/', views.release_lock, name='release_lock'),
    path('notebooks/<int:notebook_id>/check-lock/', views.check_lock_status, name='check_lock_status'),
    
    # 通知
    path('invitations/count/', views.get_invitations_count, name='get_invitations_count'),
    
    # 项目下载 - 使用notebooks应用中的下载函数
    path('projects/<int:project_id>/download/pdf/', views.download_project_pdf, name='download_project_pdf'),
    path('projects/<int:project_id>/download/html/', views.download_project_html, name='download_project_html'),
] 