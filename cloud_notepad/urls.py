"""
URL configuration for cloud_notepad project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path, include

urlpatterns = [
    path('users/', include('apps.users.urls')),
    path('notes/', include('apps.notes.urls')),
    path('storage/', include('apps.storage.urls')),  # 若需要接口暴露
    path('community/', include('apps.community.urls')),
    path('', include('apps.notes.urls')),  # 默认首页指向 notes
]

