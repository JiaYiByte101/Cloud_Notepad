# cloud_notebook/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('tinymce/', include('tinymce.urls')),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('accounts/', include('accounts.urls')),
    path('notebooks/', include('notebooks.urls')),
    path('storage/', include('storage.urls')),
    path('sharing/', include('sharing.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('friends/', include('friends.urls')),
    path('collaboration/', include('collaboration.urls')),
]

# 添加媒体文件URL配置（仅在开发环境中）
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)