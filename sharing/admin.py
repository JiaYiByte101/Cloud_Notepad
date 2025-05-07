from django.contrib import admin
from .models import Like, Comment # 导入 Comment 模型


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('notebook', 'user', 'created_at')
    list_filter = ('created_at', 'notebook', 'user')
    search_fields = ('notebook__title', 'user__username')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'notebook', 'content_snippet', 'status', 'created_at', 'updated_at', 'parent_comment')
    list_filter = ('status', 'created_at', 'updated_at', 'notebook', 'user')
    search_fields = ('user__username', 'notebook__title', 'content')
    list_editable = ('status',)
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user', 'notebook', 'parent_comment') # For better performance with many users/notebooks/comments

    def content_snippet(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_snippet.short_description = "内容摘要"

    def get_queryset(self, request):
        # 优化查询，预取关联对象
        return super().get_queryset(request).select_related('user', 'notebook', 'parent_comment')
