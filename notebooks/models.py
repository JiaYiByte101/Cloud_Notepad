# notebooks/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from tinymce.models import HTMLField


class Category(models.Model):
    """笔记分类模型"""
    name = models.CharField(max_length=100, verbose_name="分类名称")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="categories", verbose_name="所属用户")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                               related_name="subcategories", verbose_name="父分类")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "分类"
        verbose_name_plural = "分类"
        ordering = ['name']

    def __str__(self):
        return self.name


class Tag(models.Model):
    """标签模型"""
    name = models.CharField(max_length=50, verbose_name="标签名称")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="tags", verbose_name="所属用户")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")

    class Meta:
        verbose_name = "标签"
        verbose_name_plural = "标签"
        ordering = ['name']
        unique_together = ['name', 'user']  # 同一用户不能创建同名标签

    def __str__(self):
        return self.name


class Notebook(models.Model):
    """笔记模型"""
    title = models.CharField(max_length=200, verbose_name="标题")
    content = HTMLField(verbose_name="内容")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notebooks", verbose_name="所属用户")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name="notebooks", verbose_name="所属分类")
    tags = models.ManyToManyField(Tag, blank=True, related_name="notebooks", verbose_name="标签")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    is_public = models.BooleanField(default=False, verbose_name="是否公开")
    is_featured = models.BooleanField(default=False, verbose_name="是否精选")

    class Meta:
        verbose_name = "笔记"
        verbose_name_plural = "笔记"
        ordering = ['-updated_at']

    def __str__(self):
        return self.title


class Attachment(models.Model):
    """笔记附件模型"""
    notebook = models.ForeignKey(Notebook, on_delete=models.CASCADE, related_name="attachments",
                                 verbose_name="所属笔记")
    file = models.FileField(upload_to='attachments/%Y/%m/', verbose_name="文件")
    file_name = models.CharField(max_length=255, verbose_name="文件名")
    file_size = models.IntegerField(verbose_name="文件大小(字节)")
    upload_time = models.DateTimeField(auto_now_add=True, verbose_name="上传时间")

    class Meta:
        verbose_name = "附件"
        verbose_name_plural = "附件"
        ordering = ['-upload_time']

    def __str__(self):
        return self.file_name