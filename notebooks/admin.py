# notebooks/admin.py

from django.contrib import admin
from .models import Category, Tag, Notebook, Attachment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'parent', 'created_at']
    list_filter = ['user']
    search_fields = ['name']

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_at']
    list_filter = ['user']
    search_fields = ['name']

@admin.register(Notebook)
class NotebookAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'category', 'created_at', 'updated_at', 'is_public', 'is_featured']
    list_filter = ['user', 'category', 'is_public', 'is_featured', 'created_at', 'updated_at']
    search_fields = ['title', 'content']
    filter_horizontal = ['tags']

@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('notebook', 'file_name', 'file_size', 'upload_time')
    search_fields = ('file_name', 'notebook__title')
    list_filter = ('upload_time',)