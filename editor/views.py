# editor/views.py (添加一个基本视图)
from django.shortcuts import render

def editor_home(request):
    return render(request, 'editor/home.html')