# notebooks/urls.py

from django.urls import path
from . import views

app_name = 'notebooks'

urlpatterns = [
    path('', views.notebook_list, name='list'),
    path('create/', views.notebook_create, name='create'),
    path('<int:notebook_id>/', views.notebook_detail, name='detail'),
    path('<int:notebook_id>/edit/', views.notebook_edit, name='edit'),
    path('<int:notebook_id>/delete/', views.notebook_delete, name='delete'),
    path('categories/', views.category_list, name='categories'),
    path('tags/', views.tag_list, name='tags'),

    # 分类管理
    path('categories/create/', views.create_category, name='create_category'),
    path('categories/edit/', views.edit_category, name='edit_category'),
    path('categories/delete/', views.delete_category, name='delete_category'),

    # 标签管理
    path('tags/create/', views.create_tag, name='create_tag'),
    path('tags/edit/', views.edit_tag, name='edit_tag'),
    path('tags/delete/', views.delete_tag, name='delete_tag'),
]