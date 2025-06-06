from django.contrib import admin
from .models import CollaborationProject, CollaborationMember, CollaborationLock, CollaborationEdit

@admin.register(CollaborationProject)
class CollaborationProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'description', 'owner__username')
    filter_horizontal = ('notebooks',)
    date_hierarchy = 'created_at'
    
@admin.register(CollaborationMember)
class CollaborationMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'project', 'role', 'status', 'invited_by', 'invited_at', 'joined_at')
    list_filter = ('role', 'status', 'invited_at', 'joined_at')
    search_fields = ('user__username', 'project__name', 'invited_by__username')
    date_hierarchy = 'invited_at'
    
@admin.register(CollaborationLock)
class CollaborationLockAdmin(admin.ModelAdmin):
    list_display = ('notebook', 'user', 'locked_at', 'expires_at', 'is_expired')
    list_filter = ('locked_at', 'expires_at')
    search_fields = ('notebook__title', 'user__username')
    date_hierarchy = 'locked_at'

@admin.register(CollaborationEdit)
class CollaborationEditAdmin(admin.ModelAdmin):
    list_display = ('project', 'notebook', 'editor', 'summary', 'edited_at')
    list_filter = ('edited_at', 'project')
    search_fields = ('summary', 'editor__username', 'project__name', 'notebook__title')
    date_hierarchy = 'edited_at'
    readonly_fields = ('edited_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project', 'notebook', 'editor')
