from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from notebooks.models import Notebook
from django.db import transaction

class CollaborationProject(models.Model):
    """多人协作项目模型"""
    name = models.CharField(max_length=200, verbose_name="项目名称")
    description = models.TextField(blank=True, verbose_name="项目描述")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owned_projects", verbose_name="项目创建者")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    notebooks = models.ManyToManyField(Notebook, related_name="collaboration_projects", verbose_name="关联笔记")
    
    class Meta:
        verbose_name = "协作项目"
        verbose_name_plural = "协作项目"
        ordering = ['-updated_at']
    
    def __str__(self):
        return self.name
        
    @property
    def members_count(self):
        """获取项目成员数量"""
        return self.members.count()

class CollaborationMember(models.Model):
    """协作项目成员模型"""
    ROLE_CHOICES = (
        ('editor', '编辑者'),
        ('viewer', '查看者'),
    )
    
    STATUS_CHOICES = (
        ('pending', '待接受'),
        ('accepted', '已接受'),
        ('rejected', '已拒绝'),
    )
    
    project = models.ForeignKey(CollaborationProject, on_delete=models.CASCADE, related_name="members", verbose_name="所属项目")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="collaboration_memberships", verbose_name="用户")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='viewer', verbose_name="角色")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', verbose_name="状态")
    invited_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="sent_invitations", verbose_name="邀请人")
    invited_at = models.DateTimeField(default=timezone.now, verbose_name="邀请时间")
    joined_at = models.DateTimeField(null=True, blank=True, verbose_name="加入时间")
    
    class Meta:
        verbose_name = "协作成员"
        verbose_name_plural = "协作成员"
        unique_together = ('project', 'user')  # 一个用户在一个项目中只能有一个成员身份
        
    def __str__(self):
        return f"{self.user.username} - {self.project.name} ({self.get_role_display()})"
        
    def accept_invitation(self):
        """接受邀请"""
        from friends.models import ChatGroup, ChatGroupMember, GroupMessage
        
        with transaction.atomic():
            self.status = 'accepted'
            self.joined_at = timezone.now()
            self.save()
            
            # 检查项目是否已有群聊
            chat_group = getattr(self.project, 'chat_group', None)
            
            if not chat_group:
                # 创建新的群聊
                chat_group = ChatGroup.objects.create(
                    name=f"{self.project.name}协作项目",
                    description=f"用于 {self.project.name} 项目的协作交流",
                    creator=self.project.owner,
                    collaboration_project=self.project
                )
                
                # 添加项目创建者为群主
                ChatGroupMember.objects.create(
                    group=chat_group,
                    user=self.project.owner,
                    role='owner'
                )
                
                # 添加已接受邀请的其他成员
                accepted_members = self.project.members.filter(status='accepted').exclude(user=self.user)
                for member in accepted_members:
                    ChatGroupMember.objects.create(
                        group=chat_group,
                        user=member.user,
                        role='member'
                    )
            
            # 将当前用户加入群聊
            ChatGroupMember.objects.get_or_create(
                group=chat_group,
                user=self.user,
                defaults={'role': 'member'}
            )
            
            # 发送系统消息通知
            GroupMessage.objects.create(
                group=chat_group,
                sender=None,  # 系统消息
                content=f"{self.user.username} 已加入协作项目",
                message_type='system'
            )
        
    def reject_invitation(self):
        """拒绝邀请"""
        self.status = 'rejected'
        self.save()

class CollaborationLock(models.Model):
    """协作笔记锁模型，防止冲突"""
    notebook = models.ForeignKey(Notebook, on_delete=models.CASCADE, related_name="locks", verbose_name="笔记")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="held_locks", verbose_name="锁定用户")
    locked_at = models.DateTimeField(default=timezone.now, verbose_name="锁定时间")
    expires_at = models.DateTimeField(verbose_name="过期时间")  # 锁的过期时间，防止长时间占用
    
    class Meta:
        verbose_name = "协作锁"
        verbose_name_plural = "协作锁"
        unique_together = ['notebook', 'user']  # 确保每个用户对每个笔记只能有一个锁
        
    def __str__(self):
        return f"{self.notebook.title} - 被 {self.user.username} 锁定"
        
    def is_expired(self):
        """检查锁是否已过期"""
        return timezone.now() > self.expires_at

class CollaborationEdit(models.Model):
    """协作修改记录模型"""
    project = models.ForeignKey(CollaborationProject, on_delete=models.CASCADE, related_name="edits", verbose_name="所属项目")
    notebook = models.ForeignKey(Notebook, on_delete=models.CASCADE, related_name="collaboration_edits", verbose_name="修改的笔记")
    editor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="collaboration_edits", verbose_name="修改者")
    summary = models.CharField(max_length=500, verbose_name="修改大纲")
    edited_at = models.DateTimeField(default=timezone.now, verbose_name="修改时间")
    
    class Meta:
        verbose_name = "协作修改记录"
        verbose_name_plural = "协作修改记录"
        ordering = ['-edited_at']
    
    def __str__(self):
        return f"{self.editor.username if self.editor else '未知用户'} 修改了 {self.notebook.title} - {self.summary[:50]}"
    
    def get_notification_message(self):
        """获取通知消息内容"""
        time_str = self.edited_at.strftime('%Y-%m-%d %H:%M:%S')
        editor_name = self.editor.username if self.editor else '未知用户'
        return f"{editor_name} 修改了项目内容：{time_str}-{self.project.name}-{self.notebook.title}：{self.summary}"
