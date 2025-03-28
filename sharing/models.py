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


class Comment(models.Model):
    """笔记评论模型"""
    notebook = models.ForeignKey(Notebook, on_delete=models.CASCADE, related_name='comments', verbose_name="笔记")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments', verbose_name="用户")
    content = models.TextField(verbose_name="评论内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="评论时间")

    class Meta:
        verbose_name = "评论"
        verbose_name_plural = "评论"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} 评论: {self.content[:20]}..."