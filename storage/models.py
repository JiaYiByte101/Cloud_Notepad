# storage/models.py

from django.db import models
from django.contrib.auth.models import User


class CloudBackupRecord(models.Model):
    """云版本备份记录模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cloud_backups', verbose_name="用户")
    cloud_path = models.CharField(max_length=500, verbose_name="云端文件路径")
    cloud_url = models.URLField(max_length=500, verbose_name="云端访问URL")
    file_size = models.PositiveIntegerField(verbose_name="文件大小(字节)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    notebook_count = models.PositiveIntegerField(verbose_name="备份笔记数量")
    version_name = models.CharField(max_length=100, blank=True, verbose_name="版本名称")

    class Meta:
        verbose_name = "云版本备份"
        verbose_name_plural = "云版本备份"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} 的云版本备份 ({self.created_at})"

    def get_version_display(self):
        """获取版本显示名称"""
        if self.version_name:
            return self.version_name
        return f"版本 {self.created_at.strftime('%Y%m%d_%H%M%S')}"

