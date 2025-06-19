# notebooks/admin.py

from django.contrib import admin
from .models import Category, Tag, Notebook

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
    list_display = ['uuid', 'title', 'user', 'category', 'created_at', 'updated_at', 'is_public', 'is_featured']
    list_filter = ['user', 'category', 'is_public', 'is_featured', 'created_at', 'updated_at']
    search_fields = ['title', 'content']
    filter_horizontal = ['tags']