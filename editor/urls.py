# editor/urls.py
from django.urls import path
from . import views

app_name = 'editor'

urlpatterns = [
    # 暂时使用一个简单的URL
    path('', views.editor_home, name='home'),
]