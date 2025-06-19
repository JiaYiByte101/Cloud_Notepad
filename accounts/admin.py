from django.contrib import admin
from .models import Profile

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'avatar')
    search_fields = ('user__username', 'user__email')
    list_filter = ('user__date_joined',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
