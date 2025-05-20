# sharing/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone # Import timezone for 5-minute rule later
from django.http import JsonResponse # For AJAX responses
from django.views.decorators.http import require_POST # For cancel_comment
from notebooks.models import Notebook
from .models import Like, Comment, CommentLike
from .forms import CommentForm
from .utils import check_sensitive_words # Import aħna l-funzjoni l-ġdida


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
    elif sort_by == 'views':
        notebooks = notebooks.order_by('-view_count', '-created_at')
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
    """查看分享的笔记详情，处理评论的创建和重写"""
    notebook = get_object_or_404(Notebook, id=notebook_id, is_public=True)
    
    # 增加浏览量
    notebook.increment_view_count()
    
    user_liked = Like.objects.filter(notebook=notebook, user=request.user).exists()
    
    # 获取评论 - 只显示已发表的，或者属于当前用户但未发表的 (待审核/不合规)
    comments = Comment.objects.filter(
        Q(notebook=notebook, status='PUBLISHED') |
        Q(notebook=notebook, user=request.user, status__in=['PENDING', 'INAPPROPRIATE'])
    ).select_related('user', 'parent_comment').prefetch_related('replies', 'likes')

    # 为每个评论添加当前用户信息
    for comment in comments:
        comment._request = request
        for reply in comment.replies.all():
            reply._request = request

    if request.method == 'POST':
        comment_id = request.POST.get('comment_id')
        parent_comment_id = request.POST.get('parent_comment_id')
        instance_to_edit = None
        
        if comment_id:
            # This is a rewrite attempt
            instance_to_edit = get_object_or_404(Comment, id=comment_id, user=request.user, notebook=notebook)
        
        comment_form = CommentForm(request.POST, instance=instance_to_edit)

        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            
            if not instance_to_edit:  # If it's a new comment
                comment.notebook = notebook
                comment.user = request.user
                if parent_comment_id:
                    comment.parent_comment = get_object_or_404(Comment, id=parent_comment_id, notebook=notebook)
            
            content = comment_form.cleaned_data.get('content')
            is_sensitive, sensitive_word = check_sensitive_words(content)
            
            if is_sensitive:
                comment.status = 'INAPPROPRIATE'
                messages.error(request, f'您的评论包含不当内容"{sensitive_word}"，已被标记为不合规。请修改后重新提交。')
            else:
                # 自动将评论设置为已发表状态，无需人工审核
                comment.status = 'PUBLISHED'
                if instance_to_edit:
                    messages.success(request, '评论修改成功！')
                else:
                    messages.success(request, '评论发表成功！')
            
            comment.save()  # Save new or updated comment
            return redirect('sharing:view_note', notebook_id=notebook.id)
        else:
            # Form is not valid, errors will be displayed by the template
            if instance_to_edit:
                messages.error(request, "评论修改失败，请检查表单错误。")
            else:
                messages.error(request, "评论发表失败，请检查表单错误。")
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
@require_POST
def toggle_comment_like(request, comment_id):
    """点赞/取消点赞评论"""
    comment = get_object_or_404(Comment, id=comment_id)
    
    # 检查是否已点赞
    like_exists = CommentLike.objects.filter(comment=comment, user=request.user).exists()

    if like_exists:
        # 如果已点赞，则取消点赞
        CommentLike.objects.filter(comment=comment, user=request.user).delete()
        liked = False
    else:
        # 如果未点赞，则添加点赞
        CommentLike.objects.create(comment=comment, user=request.user)
        liked = True

    return JsonResponse({
        'success': True,
        'liked': liked,
        'like_count': comment.like_count
    })


@login_required
@require_POST
def delete_comment(request, comment_id):
    """删除评论"""
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    
    # 检查是否是回复评论
    if comment.parent_comment:
        # 如果是回复评论，直接删除
        comment.delete()
    else:
        # 如果是主评论，同时删除所有回复
        Comment.objects.filter(parent_comment=comment).delete()
        comment.delete()
    
    return JsonResponse({'success': True})


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