# dashboard/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Count
from notebooks.models import Notebook, Category, Tag
from django.contrib.auth.models import User
from sharing.models import Like, Comment


def is_admin(user):
    """检查用户是否是管理员"""
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_admin)
def dashboard_home(request):
    """管理员仪表板首页"""
    # 获取系统统计数据
    total_users = User.objects.count()
    total_notebooks = Notebook.objects.count()
    public_notebooks = Notebook.objects.filter(is_public=True).count()
    featured_notebooks = Notebook.objects.filter(is_featured=True).count()
    total_categories = Category.objects.count()
    total_tags = Tag.objects.count()
    total_likes = Like.objects.count()
    total_comments = Comment.objects.count()

    # 最近加入的用户
    recent_users = User.objects.order_by('-date_joined')[:5]

    # 最新的公开笔记
    latest_public_notebooks = Notebook.objects.filter(is_public=True).order_by('-created_at')[:5]

    # 最受欢迎的笔记（点赞数最多）
    popular_notebooks = Notebook.objects.filter(is_public=True) \
                            .annotate(like_count=Count('likes')) \
                            .order_by('-like_count')[:5]

    context = {
        'total_users': total_users,
        'total_notebooks': total_notebooks,
        'public_notebooks': public_notebooks,
        'featured_notebooks': featured_notebooks,
        'total_categories': total_categories,
        'total_tags': total_tags,
        'total_likes': total_likes,
        'total_comments': total_comments,
        'recent_users': recent_users,
        'latest_public_notebooks': latest_public_notebooks,
        'popular_notebooks': popular_notebooks
    }
    return render(request, 'dashboard/dashboard_home.html', context)


@login_required
@user_passes_test(is_admin)
def manage_public_notes(request):
    """管理公开笔记"""
    notebooks = Notebook.objects.filter(is_public=True).order_by('-created_at')

    return render(request, 'dashboard/manage_public_notes.html', {
        'notebooks': notebooks
    })


@login_required
@user_passes_test(is_admin)
def toggle_featured(request, notebook_id):
    """设置/取消精选笔记"""
    notebook = get_object_or_404(Notebook, id=notebook_id, is_public=True)

    notebook.is_featured = not notebook.is_featured
    notebook.save()

    if notebook.is_featured:
        messages.success(request, f'笔记 "{notebook.title}" 已设为精选！')
    else:
        messages.success(request, f'笔记 "{notebook.title}" 已取消精选。')

    return redirect('dashboard:manage_public_notes')


@login_required
@user_passes_test(is_admin)
def unpublish_note(request, notebook_id):
    """取消发布笔记（设为私有）"""
    notebook = get_object_or_404(Notebook, id=notebook_id)

    notebook.is_public = False
    notebook.is_featured = False  # 同时取消精选状态
    notebook.save()

    messages.success(request, f'笔记 "{notebook.title}" 已设为私有。')
    return redirect('dashboard:manage_public_notes')


@login_required
@user_passes_test(is_admin)
def manage_users(request):
    """管理用户"""
    users = User.objects.all().order_by('-date_joined')

    context = {
        'users': users
    }
    return render(request, 'dashboard/manage_users.html', context)