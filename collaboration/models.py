from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from notebooks.models import Notebook

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
        self.status = 'accepted'
        self.joined_at = timezone.now()
        self.save()
        
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
        
    def __str__(self):
        return f"{self.notebook.title} - 被 {self.user.username} 锁定"
        
    def is_expired(self):
        """检查锁是否已过期"""
        return timezone.now() > self.expires_at
