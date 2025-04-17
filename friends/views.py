from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q, Sum, Count
from django.http import JsonResponse
from django.utils import timezone

from .models import FriendRequest, Friendship, Message
from .forms import FriendSearchForm, MessageForm

# 工具函数：获取未读好友请求总数和未读消息总数
def get_notification_counts(user):
    pending_requests_count = FriendRequest.objects.filter(receiver=user, status='pending').count()
    unread_messages_count = Message.objects.filter(receiver=user, is_read=False).count()
    return {
        'pending_requests_count': pending_requests_count,
        'unread_messages_count': unread_messages_count,
        'total_count': pending_requests_count + unread_messages_count
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
            'timestamp': message.created_at.strftime('%Y-%m-%d %H:%M')
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
                'timestamp': msg.created_at.strftime('%Y-%m-%d %H:%M')
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
