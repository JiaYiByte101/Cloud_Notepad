from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
import logging
from django.template.loader import render_to_string
from django.utils.text import slugify
from io import BytesIO
import os
from xhtml2pdf import pisa
from django.urls import reverse

from .models import CollaborationProject, CollaborationMember, CollaborationLock
from notebooks.models import Notebook
from friends.models import Friendship, Message

# Create your views here.

# 多人协作项目视图
@login_required
def project_list(request):
    """显示用户参与的协作项目列表"""
    # 获取用户创建的项目
    owned_projects = CollaborationProject.objects.filter(owner=request.user)
    
    # 获取用户被邀请参与的已接受项目
    member_projects = CollaborationProject.objects.filter(
        members__user=request.user,
        members__status='accepted'
    ).exclude(owner=request.user)  # 排除自己创建的项目
    
    # 获取待处理的邀请
    pending_invitations = CollaborationMember.objects.filter(
        user=request.user,
        status='pending'
    )
    
    context = {
        'owned_projects': owned_projects,
        'member_projects': member_projects,
        'pending_invitations': pending_invitations
    }
    return render(request, 'collaboration/project_list.html', context)

# 协作邀请通知
@login_required
def get_invitations_count(request):
    """获取当前用户待处理的协作邀请数量"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # 查询待处理的协作邀请数量
        pending_invitations_count = CollaborationMember.objects.filter(
            user=request.user,
            status='pending'
        ).count()
        
        return JsonResponse({
            'pending_invitations_count': pending_invitations_count
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def project_detail(request, project_id):
    """查看协作项目详情"""
    # 检查用户是否有权限查看此项目
    project = get_object_or_404(
        CollaborationProject.objects.prefetch_related('members', 'notebooks'),
        id=project_id
    )
    
    # 验证用户是项目所有者或已接受邀请的成员
    if project.owner != request.user and not project.members.filter(user=request.user, status='accepted').exists():
        messages.error(request, "您没有权限查看该协作项目")
        return redirect('collaboration:project_list')
    
    # 获取项目成员
    members = project.members.all()
    
    # 获取项目关联的笔记
    notebooks = project.notebooks.all()
    
    # 检查哪些笔记当前被锁定
    locked_notebooks = {}
    for notebook in notebooks:
        try:
            lock = notebook.locks.latest('locked_at')
            if not lock.is_expired():
                locked_notebooks[notebook.id] = {
                    'user': lock.user.username,
                    'expires_at': lock.expires_at
                }
        except CollaborationLock.DoesNotExist:
            pass
    
    context = {
        'project': project,
        'members': members,
        'notebooks': notebooks,
        'locked_notebooks': locked_notebooks,
        'is_owner': project.owner == request.user
    }
    return render(request, 'collaboration/project_detail.html', context)

@login_required
def create_project(request):
    """创建新的协作项目"""
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        notebook_ids = request.POST.getlist('notebooks')
        
        if not name:
            messages.error(request, "项目名称不能为空")
            return redirect('collaboration:create_project')
        
        # 创建项目
        project = CollaborationProject.objects.create(
            name=name,
            description=description,
            owner=request.user
        )
        
        # 添加关联笔记
        if notebook_ids:
            notebooks = Notebook.objects.filter(id__in=notebook_ids, user=request.user)
            project.notebooks.add(*notebooks)
        
        messages.success(request, f"协作项目 '{name}' 创建成功")
        return redirect('collaboration:project_detail', project_id=project.id)
    
    # 获取用户的笔记
    notebooks = Notebook.objects.filter(user=request.user)
    
    context = {
        'notebooks': notebooks
    }
    return render(request, 'collaboration/project_form.html', context)

@login_required
def edit_project(request, project_id):
    """编辑协作项目"""
    project = get_object_or_404(CollaborationProject, id=project_id)
    
    # 检查权限
    if project.owner != request.user:
        messages.error(request, "只有项目创建者可以编辑项目")
        return redirect('collaboration:project_detail', project_id=project.id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        notebook_ids = request.POST.getlist('notebooks')
        
        if not name:
            messages.error(request, "项目名称不能为空")
            return redirect('collaboration:edit_project', project_id=project.id)
        
        # 更新项目信息
        project.name = name
        project.description = description
        project.save()
        
        # 更新关联笔记
        if notebook_ids:
            notebooks = Notebook.objects.filter(id__in=notebook_ids, user=request.user)
            project.notebooks.set(notebooks)
        else:
            project.notebooks.clear()
        
        messages.success(request, "协作项目更新成功")
        return redirect('collaboration:project_detail', project_id=project.id)
    
    # 获取用户的笔记
    notebooks = Notebook.objects.filter(user=request.user)
    selected_notebooks = project.notebooks.all()
    
    context = {
        'project': project,
        'notebooks': notebooks,
        'selected_notebooks': selected_notebooks
    }
    return render(request, 'collaboration/project_form.html', context)

@login_required
def delete_project(request, project_id):
    """删除协作项目"""
    project = get_object_or_404(CollaborationProject, id=project_id)
    
    # 检查权限
    if project.owner != request.user:
        messages.error(request, "只有项目创建者可以删除项目")
        return redirect('collaboration:project_detail', project_id=project.id)
    
    if request.method == 'POST':
        name = project.name
        project.delete()
        messages.success(request, f"协作项目 '{name}' 已删除")
        return redirect('collaboration:project_list')
    
    return render(request, 'collaboration/project_confirm_delete.html', {'project': project})

# 成员管理视图
@login_required
def invite_member(request, project_id):
    """邀请好友加入协作项目"""
    project = get_object_or_404(CollaborationProject, id=project_id)
    
    # 检查权限
    if project.owner != request.user and not project.members.filter(user=request.user, status='accepted', role='editor').exists():
        messages.error(request, "您没有权限邀请成员")
        return redirect('collaboration:project_detail', project_id=project.id)
    
    if request.method == 'POST':
        friend_id = request.POST.get('friend_id')
        role = request.POST.get('role', 'viewer')
        
        if not friend_id:
            messages.error(request, "请选择要邀请的好友")
            return redirect('collaboration:invite_member', project_id=project.id)
        
        # 验证是否是好友关系
        is_friend = Friendship.objects.filter(
            (Q(user=request.user) & Q(friend_id=friend_id)) |
            (Q(user_id=friend_id) & Q(friend=request.user))
        ).exists()
        
        if not is_friend:
            messages.error(request, "只能邀请您的好友加入协作项目")
            return redirect('collaboration:invite_member', project_id=project.id)
        
        from django.contrib.auth.models import User
        friend = get_object_or_404(User, id=friend_id)
        
        # 检查是否已经是成员或已邀请
        existing_member = CollaborationMember.objects.filter(
            project=project,
            user=friend
        ).first()
        
        if existing_member:
            if existing_member.status == 'accepted':
                messages.warning(request, f"{friend.username} 已是项目成员")
            elif existing_member.status == 'pending':
                messages.warning(request, f"已向 {friend.username} 发送过邀请，等待回复中")
            else:  # rejected
                # 重新发送邀请
                existing_member.status = 'pending'
                existing_member.role = role
                existing_member.invited_by = request.user
                existing_member.invited_at = timezone.now()
                existing_member.save()
                
                # 不再通过消息系统发送邀请通知
                messages.success(request, f"已重新向 {friend.username} 发送邀请")
        else:
            # 创建新邀请
            CollaborationMember.objects.create(
                project=project,
                user=friend,
                role=role,
                invited_by=request.user
            )
            
            # 不再通过消息系统发送邀请通知
            messages.success(request, f"已向 {friend.username} 发送邀请")
        
        return redirect('collaboration:project_detail', project_id=project.id)
    
    # 获取用户的好友列表
    friendships = Friendship.objects.filter(user=request.user)
    friends = [friendship.friend for friendship in friendships]
    
    # 排除已是成员的好友
    existing_member_ids = project.members.filter(status='accepted').values_list('user_id', flat=True)
    available_friends = [friend for friend in friends if friend.id not in existing_member_ids]
    
    context = {
        'project': project,
        'available_friends': available_friends
    }
    return render(request, 'collaboration/invite_member.html', context)

@login_required
def handle_invitation(request, member_id, action):
    """处理协作项目邀请（接受或拒绝）"""
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"处理邀请: 用户={request.user.username}, 成员ID={member_id}, 操作={action}, 方法={request.method}")
        
        # 确保请求方法是POST
        if request.method != 'POST':
            logger.warning(f"非POST请求: 用户={request.user.username}, 方法={request.method}")
            messages.error(request, "无效的请求方法")
            return redirect('collaboration:project_list')
            
        membership = get_object_or_404(CollaborationMember, id=member_id, user=request.user, status='pending')
        project = membership.project
        logger.info(f"找到待处理邀请: 项目={project.name}, 邀请人={membership.invited_by}")
        
        if action == 'accept':
            logger.info(f"用户接受邀请: 用户={request.user.username}, 项目={project.name}")
            membership.accept_invitation()
            messages.success(request, f"您已接受加入协作项目 '{project.name}'")
        elif action == 'reject':
            logger.info(f"用户拒绝邀请: 用户={request.user.username}, 项目={project.name}")
            membership.reject_invitation()
            messages.success(request, f"您已拒绝加入协作项目 '{project.name}'")
        else:
            logger.warning(f"无效操作: 用户={request.user.username}, 操作={action}")
            messages.error(request, f"无效的操作: {action}")
        
        # 不再通过消息系统发送回复通知
        return redirect('collaboration:project_list')
    except CollaborationMember.DoesNotExist:
        logger.error(f"邀请不存在: 用户={request.user.username}, 成员ID={member_id}")
        messages.error(request, "找不到相关邀请")
        return redirect('collaboration:project_list')
    except Exception as e:
        # 记录详细错误信息
        logger.error(f"处理邀请时发生错误: {str(e)}", exc_info=True)
        
        # 处理可能出现的错误
        messages.error(request, f"处理邀请时发生错误，请稍后再试")
        return redirect('collaboration:project_list')

@login_required
def remove_member(request, project_id, member_id):
    """从协作项目中移除成员"""
    project = get_object_or_404(CollaborationProject, id=project_id)
    membership = get_object_or_404(CollaborationMember, id=member_id, project=project)
    
    # 检查权限
    if project.owner != request.user and membership.user != request.user:
        messages.error(request, "您没有权限执行此操作")
        return redirect('collaboration:project_detail', project_id=project.id)
    
    user_to_remove = membership.user
    is_self_leaving = user_to_remove == request.user
    
    membership.delete()
    
    if is_self_leaving:
        messages.success(request, f"您已退出协作项目 '{project.name}'")
        return redirect('collaboration:project_list')
    else:
        messages.success(request, f"{user_to_remove.username} 已从项目中移除")
        return redirect('collaboration:project_detail', project_id=project.id)

@login_required
def change_member_role(request, member_id):
    """更改协作成员角色"""
    membership = get_object_or_404(CollaborationMember, id=member_id)
    project = membership.project
    
    # 检查权限
    if project.owner != request.user:
        messages.error(request, "只有项目创建者可以更改成员角色")
        return redirect('collaboration:project_detail', project_id=project.id)
    
    if request.method == 'POST':
        new_role = request.POST.get('role')
        if new_role in dict(CollaborationMember.ROLE_CHOICES):
            membership.role = new_role
            membership.save()
            messages.success(request, f"{membership.user.username} 的角色已更新为 {membership.get_role_display()}")
        else:
            messages.error(request, "无效的角色选择")
    
    return redirect('collaboration:project_detail', project_id=project.id)

# 笔记锁定视图
@login_required
def lock_notebook(request, notebook_id):
    """锁定协作笔记进行编辑"""
    notebook = get_object_or_404(Notebook, id=notebook_id)
    
    # 验证用户有权编辑该笔记
    has_permission = False
    
    # 如果是笔记所有者，直接有权限
    if notebook.user == request.user:
        has_permission = True
    else:
        # 如果是协作项目成员
        projects = notebook.collaboration_projects.all()
        for project in projects:
            if project.owner == request.user or project.members.filter(
                user=request.user, 
                status='accepted',
                role='editor'
            ).exists():
                has_permission = True
                break
    
    if not has_permission:
        return JsonResponse({
            'success': False, 
            'message': '您没有权限编辑此笔记'
        })
    
    # 检查笔记是否已被锁定
    try:
        current_lock = CollaborationLock.objects.filter(notebook=notebook).latest('locked_at')
        if not current_lock.is_expired() and current_lock.user != request.user:
            return JsonResponse({
                'success': False,
                'message': f'此笔记当前被 {current_lock.user.username} 锁定，请稍后再试',
                'locked_by': current_lock.user.username,
                'expires_at': current_lock.expires_at.isoformat()
            })
    except CollaborationLock.DoesNotExist:
        pass
    
    # 创建或更新锁
    lock_duration = timedelta(minutes=30)  # 锁定30分钟
    expires_at = timezone.now() + lock_duration
    
    lock, created = CollaborationLock.objects.update_or_create(
        notebook=notebook,
        user=request.user,
        defaults={'expires_at': expires_at}
    )
    
    return JsonResponse({
        'success': True,
        'message': '笔记已锁定，您可以安全地进行编辑',
        'expires_at': expires_at.isoformat()
    })

@login_required
def release_lock(request, notebook_id):
    """释放笔记编辑锁"""
    notebook = get_object_or_404(Notebook, id=notebook_id)
    
    # 尝试查找并删除该用户对该笔记的锁
    lock = CollaborationLock.objects.filter(notebook=notebook, user=request.user).delete()
    
    return JsonResponse({
        'success': True,
        'message': '笔记锁已释放'
    })

@login_required
def check_lock_status(request, notebook_id):
    """检查笔记的锁定状态"""
    notebook = get_object_or_404(Notebook, id=notebook_id)
    
    try:
        lock = CollaborationLock.objects.filter(notebook=notebook).latest('locked_at')
        if lock.is_expired():
            # 如果锁已过期，则删除
            lock.delete()
            return JsonResponse({
                'locked': False,
                'message': '笔记未被锁定'
            })
        else:
            return JsonResponse({
                'locked': True,
                'locked_by': lock.user.username,
                'is_self': lock.user == request.user,
                'expires_at': lock.expires_at.isoformat(),
                'message': '笔记被锁定' if lock.user == request.user else f'笔记当前被 {lock.user.username} 锁定'
            })
    except CollaborationLock.DoesNotExist:
        return JsonResponse({
            'locked': False,
            'message': '笔记未被锁定'
        })

@login_required
def download_project_pdf(request, project_id):
    """下载协作项目为PDF格式 - 适配notebooks应用的下载逻辑"""
    # 获取项目并验证权限
    project = get_object_or_404(CollaborationProject, id=project_id)
    if project.owner != request.user and not project.members.filter(user=request.user, status='accepted').exists():
        messages.error(request, "您没有权限下载该协作项目")
        return redirect('collaboration:project_list')
    
    # 确保项目有关联的笔记本
    if not project.notebooks.exists():
        messages.error(request, "该项目没有关联的笔记本，无法下载")
        return redirect('collaboration:project_detail', project_id=project.id)
    
    # 获取项目的第一个笔记本用于下载
    notebook_id = project.notebooks.first().id
    
    # 重定向到notebooks的下载功能
    redirect_url = reverse('notebooks:download_pdf', args=[notebook_id])
    return redirect(redirect_url)

@login_required
def download_project_html(request, project_id):
    """下载协作项目为HTML格式 - 适配notebooks应用的下载逻辑"""
    # 获取项目并验证权限
    project = get_object_or_404(CollaborationProject, id=project_id)
    if project.owner != request.user and not project.members.filter(user=request.user, status='accepted').exists():
        messages.error(request, "您没有权限下载该协作项目")
        return redirect('collaboration:project_list')
    
    # 确保项目有关联的笔记本
    if not project.notebooks.exists():
        messages.error(request, "该项目没有关联的笔记本，无法下载")
        return redirect('collaboration:project_detail', project_id=project.id)
    
    # 获取项目的第一个笔记本用于下载
    notebook_id = project.notebooks.first().id
    
    # 重定向到notebooks的下载功能
    redirect_url = reverse('notebooks:download_html', args=[notebook_id])
    return redirect(redirect_url)
