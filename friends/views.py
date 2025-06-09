from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.utils import timezone
from django.template.defaultfilters import date as date_filter
from .models import FriendRequest, Friendship, Message, ChatGroup, ChatGroupMember, GroupMessage, MessageReadStatus
import json
import pytz

from .forms import FriendSearchForm, MessageForm

def format_message_time(dt):
    """
    将UTC时间转换为北京时间并格式化
    """
    # 确保时间是aware的
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.utc)
    
    # 转换为北京时间
    beijing_tz = pytz.timezone('Asia/Shanghai')
    beijing_time = dt.astimezone(beijing_tz)
    
    # 格式化为字符串
    return beijing_time.strftime('%Y-%m-%d %H:%M')

def get_user_unread_group_messages_count(user):
    """
    获取用户的群聊未读消息数量
    这个函数提供更准确的未读消息统计
    """
    # 获取用户参与的所有活跃群聊
    user_groups = ChatGroup.objects.filter(
        members__user=user,
        members__is_active=True,
        is_active=True
    )
    
    total_unread = 0
    for group in user_groups:
        # 获取该群聊中用户未读的消息数量
        unread_count = GroupMessage.objects.filter(
            group=group
        ).exclude(
            messagereadstatus__user=user
        ).count()
        total_unread += unread_count
    
    return total_unread

# 工具函数：获取未读好友请求总数和未读消息总数
def get_notification_counts(user):
    pending_requests_count = FriendRequest.objects.filter(receiver=user, status='pending').count()
    unread_messages_count = Message.objects.filter(receiver=user, is_read=False).count()
    
    # 获取群聊未读消息数量
    unread_group_messages_count = get_user_unread_group_messages_count(user)
    
    return {
        'pending_requests_count': pending_requests_count,
        'unread_messages_count': unread_messages_count,
        'unread_group_messages_count': unread_group_messages_count,
        'total_count': pending_requests_count + unread_messages_count + unread_group_messages_count
    }

@login_required
def friends_home(request):
    """好友主页，显示好友列表和相关功能入口"""
    user_friendships = Friendship.objects.filter(user=request.user)
    friends = [friendship.friend for friendship in user_friendships]
    
    # 获取通知数量
    notification_counts = get_notification_counts(request.user)
    
    context = {
        'friends': friends,
        'pending_requests': notification_counts['pending_requests_count'],
        'search_form': FriendSearchForm(),
    }
    return render(request, 'friends/home.html', context)

@login_required
def search_users(request):
    """搜索用户功能"""
    if request.method == 'POST':
        form = FriendSearchForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            # 根据用户名或邮箱搜索，排除自己
            users = User.objects.filter(
                Q(username__icontains=query) | Q(email__icontains=query)
            ).exclude(id=request.user.id)
            
            # 获取好友关系状态
            user_friendships = list(Friendship.objects.filter(user=request.user).values_list('friend_id', flat=True))
            friend_requests_sent = list(FriendRequest.objects.filter(
                sender=request.user, status='pending'
            ).values_list('receiver_id', flat=True))
            friend_requests_received = list(FriendRequest.objects.filter(
                receiver=request.user, status='pending'
            ).values_list('sender_id', flat=True))
            
            return render(request, 'friends/search_results.html', {
                'users': users,
                'query': query,
                'user_friendships': user_friendships,
                'friend_requests_sent': friend_requests_sent,
                'friend_requests_received': friend_requests_received,
            })
    else:
        form = FriendSearchForm()
    
    return render(request, 'friends/search.html', {'form': form})

@login_required
def send_friend_request(request, user_id):
    """发送好友请求"""
    receiver = get_object_or_404(User, id=user_id)
    
    # 检查是否已经是好友
    if Friendship.objects.filter(user=request.user, friend=receiver).exists():
        messages.warning(request, f'您已经是 {receiver.username} 的好友')
        return redirect('friends:search_users')
    
    # 检查是否已经发送过请求
    if FriendRequest.objects.filter(sender=request.user, receiver=receiver).exists():
        messages.info(request, f'您已经向 {receiver.username} 发送过好友请求')
        return redirect('friends:search_users')
    
    # 创建好友请求
    FriendRequest.objects.create(sender=request.user, receiver=receiver)
    messages.success(request, f'已向 {receiver.username} 发送好友请求')
    return redirect('friends:search_users')

@login_required
def friend_requests(request):
    """显示收到的好友请求"""
    # 获取所有待处理的好友请求
    pending_requests = FriendRequest.objects.filter(receiver=request.user, status='pending')
    
    # 将请求标记为已查看（虽然这个模型没有已查看字段，但之后的通知计数会反映这一点）
    # 因为我们会在导航栏中使用实时查询，所以用户来过这个页面就意味着已经看到了通知
    
    return render(request, 'friends/requests.html', {'pending_requests': pending_requests})

@login_required
def accept_friend_request(request, request_id):
    """接受好友请求"""
    friend_request = get_object_or_404(FriendRequest, id=request_id, receiver=request.user)
    
    if friend_request.status != 'pending':
        messages.warning(request, '该请求已被处理')
        return redirect('friends:friend_requests')
    
    # 更新请求状态为已接受
    friend_request.status = 'accepted'
    friend_request.save()
    
    # 创建双向好友关系
    Friendship.objects.create(user=request.user, friend=friend_request.sender)
    Friendship.objects.create(user=friend_request.sender, friend=request.user)
    
    messages.success(request, f'您已接受 {friend_request.sender.username} 的好友请求')
    return redirect('friends:friend_requests')

@login_required
def reject_friend_request(request, request_id):
    """拒绝好友请求"""
    friend_request = get_object_or_404(FriendRequest, id=request_id, receiver=request.user)
    
    if friend_request.status != 'pending':
        messages.warning(request, '该请求已被处理')
        return redirect('friends:friend_requests')
    
    # 更新请求状态为已拒绝
    friend_request.status = 'rejected'
    friend_request.save()
    
    messages.success(request, f'您已拒绝 {friend_request.sender.username} 的好友请求')
    return redirect('friends:friend_requests')

@login_required
def remove_friend(request, friend_id):
    """删除好友"""
    friend = get_object_or_404(User, id=friend_id)
    
    # 删除双向好友关系
    Friendship.objects.filter(user=request.user, friend=friend).delete()
    Friendship.objects.filter(user=friend, friend=request.user).delete()
    
    messages.success(request, f'您已将 {friend.username} 从好友列表中移除')
    return redirect('friends:home')

@login_required
def chat_list(request):
    """显示聊天列表"""
    # 获取用户的所有好友
    friendships = Friendship.objects.filter(user=request.user)
    friends = [friendship.friend for friendship in friendships]
    
    # 对每个好友，获取最新的一条消息
    chats = []
    for friend in friends:
        latest_message = Message.objects.filter(
            Q(sender=request.user, receiver=friend) | Q(sender=friend, receiver=request.user)
        ).order_by('-created_at').first()
        
        if latest_message:
            # 检查是否有未读消息
            unread_count = Message.objects.filter(
                sender=friend, receiver=request.user, is_read=False
            ).count()
            
            chats.append({
                'friend': friend,
                'latest_message': latest_message,
                'unread_count': unread_count,
            })
    
    # 按最后消息时间排序
    chats.sort(key=lambda x: x['latest_message'].created_at if x.get('latest_message') else timezone.now(), reverse=True)
    
    return render(request, 'friends/chat_list.html', {'chats': chats})

@login_required
def chat_detail(request, friend_id):
    """显示与特定好友的聊天详情"""
    friend = get_object_or_404(User, id=friend_id)
    
    # 确认是否是好友关系
    if not Friendship.objects.filter(user=request.user, friend=friend).exists():
        messages.error(request, '您不是该用户的好友，无法进行聊天')
        return redirect('friends:chat_list')
    
    # 获取聊天记录
    messages_list = Message.objects.filter(
        Q(sender=request.user, receiver=friend) | Q(sender=friend, receiver=request.user)
    ).order_by('created_at')
    
    # 将所有接收到的消息标记为已读
    unread_messages = Message.objects.filter(sender=friend, receiver=request.user, is_read=False)
    if unread_messages.exists():
        unread_count = unread_messages.count()
        unread_messages.update(is_read=True)
        messages.info(request, f'已将 {unread_count} 条未读消息标记为已读')
    
    # 处理新消息提交
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.receiver = friend
            message.save()
            return redirect('friends:chat_detail', friend_id=friend_id)
    else:
        form = MessageForm()
    
    context = {
        'friend': friend,
        'messages_list': messages_list,
        'form': form,
    }
    return render(request, 'friends/chat_detail.html', context)

@login_required
def send_message_ajax(request, friend_id):
    """通过AJAX发送消息"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        friend = get_object_or_404(User, id=friend_id)
        content = request.POST.get('content', '').strip()
        
        if not content:
            return JsonResponse({'status': 'error', 'message': '消息不能为空'})
        
        # 创建新消息
        message = Message.objects.create(
            sender=request.user,
            receiver=friend,
            content=content
        )
        
        return JsonResponse({
            'status': 'success',
            'message_id': message.id,
            'content': message.content,
            'timestamp': format_message_time(message.created_at)
        })
    
    return JsonResponse({'status': 'error', 'message': '无效的请求'})

@login_required
def get_new_messages_ajax(request, friend_id):
    """通过AJAX获取新消息"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        friend = get_object_or_404(User, id=friend_id)
        last_message_id = request.GET.get('last_id', 0)
        
        # 获取新消息
        new_messages = Message.objects.filter(
            Q(sender=friend, receiver=request.user) | Q(sender=request.user, receiver=friend),
            id__gt=last_message_id
        ).order_by('created_at')
        
        # 将接收到的新消息标记为已读
        unread_messages = new_messages.filter(sender=friend, receiver=request.user, is_read=False)
        for msg in unread_messages:
            msg.is_read = True
            msg.save()
        
        # 准备消息数据
        messages_data = []
        for msg in new_messages:
            messages_data.append({
                'id': msg.id,
                'content': msg.content,
                'sender_id': msg.sender.id,
                'is_self': msg.sender.id == request.user.id,
                'timestamp': format_message_time(msg.created_at)
            })
        
        return JsonResponse({'messages': messages_data})
    
    return JsonResponse({'status': 'error', 'message': '无效的请求'})

@login_required
def get_notifications_count_ajax(request):
    """通过AJAX获取通知数量"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        counts = get_notification_counts(request.user)
        return JsonResponse(counts)
    
    return JsonResponse({'status': 'error', 'message': '无效的请求'})

@login_required
def group_list(request):
    """显示用户所在的群聊列表"""
    # 获取用户参与的所有群聊
    user_groups = ChatGroup.objects.filter(
        members__user=request.user,
        members__is_active=True,
        is_active=True
    ).order_by('-updated_at')
    
    # 为每个群聊计算未读消息数量
    groups_with_unread = []
    for group in user_groups:
        # 计算该群聊中用户未读的消息数量
        unread_count = GroupMessage.objects.filter(
            group=group
        ).exclude(
            messagereadstatus__user=request.user
        ).count()
        
        # 将未读数量添加到群聊对象
        group.unread_count = unread_count
        groups_with_unread.append(group)
    
    context = {
        'groups': groups_with_unread,
    }
    return render(request, 'friends/group_list.html', context)

@login_required
def group_chat_detail(request, group_id):
    """群聊详情页面"""
    group = get_object_or_404(ChatGroup, id=group_id, is_active=True)
    
    # 检查用户是否是群成员
    membership = group.members.filter(user=request.user, is_active=True).first()
    if not membership:
        messages.error(request, '您不是该群聊的成员')
        return redirect('friends:group_list')
    
    # 获取群聊消息（最近100条）
    messages_list = group.messages.select_related('sender').order_by('-created_at')[:100][::-1]
    
    # 标记消息为已读
    unread_messages = group.messages.exclude(read_by=request.user)
    for msg in unread_messages:
        MessageReadStatus.objects.get_or_create(message=msg, user=request.user)
    
    # 确保所有消息都被标记为已读（包括刚刚创建的已读状态）
    # 这一步是为了确保数据一致性
    all_messages = group.messages.all()
    for msg in all_messages:
        if not msg.read_by.filter(id=request.user.id).exists():
            MessageReadStatus.objects.get_or_create(message=msg, user=request.user)
    
    # 更新最后阅读时间
    membership.last_read_at = timezone.now()
    membership.save()
    
    # 获取群成员列表
    members = group.members.filter(is_active=True).select_related('user')
    
    context = {
        'group': group,
        'messages_list': messages_list,  # 修改变量名避免冲突
        'members': members,
        'membership': membership,
    }
    return render(request, 'friends/group_chat_detail.html', context)

@login_required
def send_group_message_ajax(request, group_id):
    """发送群聊消息（AJAX）"""
    if request.method == 'POST':
        group = get_object_or_404(ChatGroup, id=group_id, is_active=True)
        
        # 检查用户是否是群成员
        if not group.members.filter(user=request.user, is_active=True).exists():
            return JsonResponse({'success': False, 'error': '您不是该群聊的成员'})
        
        content = request.POST.get('content', '').strip()
        if not content:
            return JsonResponse({'success': False, 'error': '消息内容不能为空'})
        
        # 创建消息
        message = GroupMessage.objects.create(
            group=group,
            sender=request.user,
            content=content,
            message_type='text'
        )
        
        # 标记自己已读
        MessageReadStatus.objects.create(message=message, user=request.user)
        
        # 更新群聊的最后活动时间
        group.updated_at = timezone.now()
        group.save()
        
        # 返回消息信息
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'sender': message.sender.username,
                'content': message.content,
                'created_at': format_message_time(message.created_at),
                'message_type': message.message_type,
            }
        })
    
    return JsonResponse({'success': False, 'error': '请求方法错误'})

@login_required
def get_new_group_messages_ajax(request, group_id):
    """获取新的群聊消息（AJAX）"""
    group = get_object_or_404(ChatGroup, id=group_id, is_active=True)
    
    # 检查用户是否是群成员
    if not group.members.filter(user=request.user, is_active=True).exists():
        return JsonResponse({'success': False, 'error': '您不是该群聊的成员'})
    
    # 获取最后一条消息的ID
    last_message_id = request.GET.get('last_message_id', 0)
    
    try:
        last_message_id = int(last_message_id)
    except:
        last_message_id = 0
    
    # 获取新消息
    new_messages = group.messages.filter(id__gt=last_message_id).select_related('sender')
    
    # 标记新消息为已读
    for msg in new_messages:
        MessageReadStatus.objects.get_or_create(message=msg, user=request.user)
    
    # 更新用户在该群聊的最后阅读时间
    membership = group.members.filter(user=request.user, is_active=True).first()
    if membership:
        membership.last_read_at = timezone.now()
        membership.save()
    
    # 构建响应数据
    messages_data = []
    for msg in new_messages:
        messages_data.append({
            'id': msg.id,
            'sender': msg.sender.username if msg.sender else '系统',
            'content': msg.content,
            'created_at': format_message_time(msg.created_at),
            'message_type': msg.message_type,
            'is_mine': msg.sender == request.user if msg.sender else False,
        })
    
    return JsonResponse({
        'success': True,
        'messages': messages_data,
        'count': len(messages_data)
    })

@login_required
def group_members(request, group_id):
    """查看群成员列表"""
    group = get_object_or_404(ChatGroup, id=group_id, is_active=True)
    
    # 检查用户是否是群成员
    if not group.members.filter(user=request.user, is_active=True).exists():
        messages.error(request, '您不是该群聊的成员')
        return redirect('friends:group_list')
    
    # 获取所有活跃成员
    members = group.members.filter(is_active=True).select_related('user').order_by('role', 'joined_at')
    
    context = {
        'group': group,
        'members': members,
    }
    return render(request, 'friends/group_members.html', context)

@login_required
def refresh_group_read_status(request):
    """
    刷新用户的群聊消息已读状态
    这是一个调试/修复功能，用于解决已读状态不同步的问题
    """
    if request.method == 'POST':
        # 获取用户参与的所有群聊
        user_groups = ChatGroup.objects.filter(
            members__user=request.user,
            members__is_active=True,
            is_active=True
        )
        
        total_marked = 0
        for group in user_groups:
            # 获取该群聊的所有消息
            all_messages = group.messages.all()
            for msg in all_messages:
                # 如果用户还没有已读记录，创建一个
                read_status, created = MessageReadStatus.objects.get_or_create(
                    message=msg, 
                    user=request.user
                )
                if created:
                    total_marked += 1
            
            # 更新最后阅读时间
            membership = group.members.filter(user=request.user, is_active=True).first()
            if membership:
                membership.last_read_at = timezone.now()
                membership.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'marked_count': total_marked,
                'message': f'已标记 {total_marked} 条消息为已读'
            })
        else:
            messages.success(request, f'已刷新群聊已读状态，标记了 {total_marked} 条消息为已读')
            return redirect('friends:group_list')
    
    return JsonResponse({'success': False, 'error': '无效的请求方法'})

@login_required
def get_group_unread_counts_ajax(request):
    """
    通过AJAX获取所有群聊的未读消息数量
    用于实时更新群聊列表页面的未读消息显示
    """
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # 获取用户参与的所有群聊
        user_groups = ChatGroup.objects.filter(
            members__user=request.user,
            members__is_active=True,
            is_active=True
        )
        
        group_counts = {}
        for group in user_groups:
            # 计算该群聊中用户未读的消息数量
            unread_count = GroupMessage.objects.filter(
                group=group
            ).exclude(
                messagereadstatus__user=request.user
            ).count()
            
            group_counts[group.id] = unread_count
        
        return JsonResponse({
            'success': True,
            'group_counts': group_counts
        })
    
    return JsonResponse({'success': False, 'error': '无效的请求'})
