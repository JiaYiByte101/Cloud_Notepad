# sharing/models.py

from django.db import models
from django.contrib.auth.models import User
from notebooks.models import Notebook


class Like(models.Model):
    """笔记点赞模型"""
    notebook = models.ForeignKey(Notebook, on_delete=models.CASCADE, related_name='likes', verbose_name="笔记")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes', verbose_name="用户")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="点赞时间")

    class Meta:
        verbose_name = "点赞"
        verbose_name_plural = "点赞"
        unique_together = ['notebook', 'user']  # 同一用户对同一笔记只能点赞一次

    def __str__(self):
        return f"{self.user.username} 点赞了 {self.notebook.title}"


class CommentLike(models.Model):
    """评论点赞模型"""
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, related_name='likes', verbose_name="评论")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comment_likes', verbose_name="用户")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="点赞时间")

    class Meta:
        verbose_name = "评论点赞"
        verbose_name_plural = "评论点赞"
        unique_together = ['comment', 'user']  # 同一用户对同一评论只能点赞一次

    def __str__(self):
        return f"{self.user.username} 点赞了评论"


class Comment(models.Model):
    """笔记评论模型"""
    notebook = models.ForeignKey(Notebook, on_delete=models.CASCADE, related_name='comments', verbose_name="笔记")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_comments', verbose_name="用户")
    content = models.TextField(verbose_name="评论内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="评论时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")

    STATUS_CHOICES = [
        ('PENDING', '待审核'),
        ('INAPPROPRIATE', '不合规'),
        ('PUBLISHED', '已发表'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="状态")

    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                                       related_name="replies", verbose_name="父评论")

    class Meta:
        verbose_name = "评论"
        verbose_name_plural = "评论"
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username} 评论: {self.content[:20]}..."

    @property
    def like_count(self):
        """获取评论点赞数"""
        return self.likes.count()

    def is_liked_by_user(self, user):
        """检查用户是否已点赞该评论"""
        return self.likes.filter(user=user).exists()