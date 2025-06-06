from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class FriendRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', '待处理'),
        ('accepted', '已接受'),
        ('rejected', '已拒绝'),
    )
    
    sender = models.ForeignKey(User, related_name='sent_requests', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('sender', 'receiver')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username} ({self.get_status_display()})"

class Friendship(models.Model):
    user = models.ForeignKey(User, related_name='friendships', on_delete=models.CASCADE)
    friend = models.ForeignKey(User, related_name='+', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ('user', 'friend')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.friend.username}"

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username} ({self.created_at.strftime('%Y-%m-%d %H:%M')})"

class ChatGroup(models.Model):
    """群聊模型"""
    name = models.CharField(max_length=200, verbose_name="群聊名称")
    description = models.TextField(blank=True, verbose_name="群聊描述")
    creator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_groups', verbose_name="创建者")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    is_active = models.BooleanField(default=True, verbose_name="是否活跃")
    
    # 关联协作项目（可选）
    collaboration_project = models.OneToOneField(
        'collaboration.CollaborationProject', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='chat_group',
        verbose_name="关联的协作项目"
    )
    
    class Meta:
        verbose_name = "群聊"
        verbose_name_plural = "群聊"
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.name
        
    @property
    def members_count(self):
        """获取群成员数量"""
        return self.members.filter(is_active=True).count()

class ChatGroupMember(models.Model):
    """群聊成员模型"""
    ROLE_CHOICES = (
        ('owner', '群主'),
        ('admin', '管理员'),
        ('member', '成员'),
    )
    
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='members', verbose_name="所属群聊")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chat_groups', verbose_name="用户")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member', verbose_name="角色")
    joined_at = models.DateTimeField(default=timezone.now, verbose_name="加入时间")
    is_active = models.BooleanField(default=True, verbose_name="是否在群内")
    last_read_at = models.DateTimeField(null=True, blank=True, verbose_name="最后阅读时间")
    
    class Meta:
        verbose_name = "群聊成员"
        verbose_name_plural = "群聊成员"
        unique_together = ('group', 'user')
        ordering = ['joined_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.group.name} ({self.get_role_display()})"

class GroupMessage(models.Model):
    """群聊消息模型"""
    MESSAGE_TYPE_CHOICES = (
        ('text', '文本消息'),
        ('system', '系统消息'),
        ('notification', '通知消息'),
    )
    
    group = models.ForeignKey(ChatGroup, on_delete=models.CASCADE, related_name='messages', verbose_name="所属群聊")
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_group_messages', verbose_name="发送者")
    content = models.TextField(verbose_name="消息内容")
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPE_CHOICES, default='text', verbose_name="消息类型")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="发送时间")
    
    # 用于记录已读状态
    read_by = models.ManyToManyField(User, through='MessageReadStatus', related_name='read_group_messages', verbose_name="已读用户")
    
    class Meta:
        verbose_name = "群聊消息"
        verbose_name_plural = "群聊消息"
        ordering = ['created_at']
    
    def __str__(self):
        sender_name = self.sender.username if self.sender else "系统"
        return f"{self.group.name} - {sender_name}: {self.content[:50]}"

class MessageReadStatus(models.Model):
    """消息已读状态模型"""
    message = models.ForeignKey(GroupMessage, on_delete=models.CASCADE, verbose_name="消息")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    read_at = models.DateTimeField(default=timezone.now, verbose_name="阅读时间")
    
    class Meta:
        verbose_name = "消息已读状态"
        verbose_name_plural = "消息已读状态"
        unique_together = ('message', 'user')
    
    def __str__(self):
        return f"{self.user.username} 已读 {self.message.id}"
