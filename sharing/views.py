# sharing/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from notebooks.models import Notebook
from .models import Like, Comment
from .forms import CommentForm


@login_required
def public_notes(request):
    """显示公开笔记"""
    search_query = request.GET.get('search')
    sort_by = request.GET.get('sort', 'recent')  # 默认按最新排序

    # 获取所有公开笔记
    notebooks = Notebook.objects.filter(is_public=True)

    # 搜索功能
    if search_query:
        notebooks = notebooks.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query)
        )

    # 排序功能
    if sort_by == 'popular':
        notebooks = notebooks.annotate(like_count=Count('likes')).order_by('-like_count', '-created_at')
    elif sort_by == 'featured':
        notebooks = notebooks.filter(is_featured=True).order_by('-created_at')
    else:  # 默认最新
        notebooks = notebooks.order_by('-created_at')

    context = {
        'notebooks': notebooks,
        'search_query': search_query,
        'sort_by': sort_by
    }
    return render(request, 'sharing/public_notes.html', context)


@login_required
def view_shared_note(request, notebook_id):
    """查看分享的笔记详情"""
    notebook = get_object_or_404(Notebook, id=notebook_id, is_public=True)

    # 检查当前用户是否已点赞
    user_liked = Like.objects.filter(notebook=notebook, user=request.user).exists()

    # 获取评论
    comments = Comment.objects.filter(notebook=notebook)

    # 评论表单
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.notebook = notebook
            comment.user = request.user
            comment.save()
            messages.success(request, '评论发布成功！')
            return redirect('sharing:view_note', notebook_id=notebook.id)
    else:
        comment_form = CommentForm()

    context = {
        'notebook': notebook,
        'user_liked': user_liked,
        'like_count': notebook.likes.count(),
        'comments': comments,
        'comment_form': comment_form
    }
    return render(request, 'sharing/view_shared_note.html', context)


@login_required
def toggle_like(request, notebook_id):
    """点赞/取消点赞功能"""
    notebook = get_object_or_404(Notebook, id=notebook_id, is_public=True)

    # 检查是否已点赞
    like_exists = Like.objects.filter(notebook=notebook, user=request.user).exists()

    if like_exists:
        # 如果已点赞，则取消点赞
        Like.objects.filter(notebook=notebook, user=request.user).delete()
        messages.success(request, '已取消点赞')
    else:
        # 如果未点赞，则添加点赞
        Like.objects.create(notebook=notebook, user=request.user)
        messages.success(request, '已点赞！')

    return redirect('sharing:view_note', notebook_id=notebook.id)