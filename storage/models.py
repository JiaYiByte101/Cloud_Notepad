# storage/models.py

from django.db import models
from django.contrib.auth.models import User
from notebooks.models import Notebook


class BackupRecord(models.Model):
    """备份记录模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='backups', verbose_name="用户")
    file_path = models.CharField(max_length=255, verbose_name="文件路径")
    file_size = models.PositiveIntegerField(verbose_name="文件大小(字节)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    notebook_count = models.PositiveIntegerField(verbose_name="备份笔记数量")

    class Meta:
        verbose_name = "备份记录"
        verbose_name_plural = "备份记录"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} 的备份 ({self.created_at})"


class SyncStatus(models.Model):
    """同步状态模型"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='sync_status', verbose_name="用户")
    last_sync = models.DateTimeField(null=True, blank=True, verbose_name="最后同步时间")
    is_syncing = models.BooleanField(default=False, verbose_name="是否正在同步")
    sync_error = models.TextField(blank=True, verbose_name="同步错误信息")

    class Meta:
        verbose_name = "同步状态"
        verbose_name_plural = "同步状态"

    def __str__(self):
        return f"{self.user.username} 的同步状态"