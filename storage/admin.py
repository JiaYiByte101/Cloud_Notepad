from django.contrib import admin
from .models import CloudBackupRecord

@admin.register(CloudBackupRecord)
class CloudBackupRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'version_name', 'notebook_count', 'file_size', 'created_at')
    list_filter = ('created_at', 'user')
    search_fields = ('user__username', 'version_name', 'cloud_path')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'cloud_url', 'cloud_path')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
