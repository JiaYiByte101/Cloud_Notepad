# accounts/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from PIL import Image
import os
import io

def user_avatar_upload_path(instance, filename):
    """生成用户头像的上传路径"""
    import uuid
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4().hex}.{ext}"
    return f"avatars/{instance.user.username}/{filename}"

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(
        blank=True,  # 允许为空
        null=True,   # 允许数据库为NULL
        upload_to=user_avatar_upload_path,
        storage=default_storage  # 明确指定使用默认存储（云存储）
    )

    class Meta:
        verbose_name = "用户档案"
        verbose_name_plural = "用户档案"
        ordering = ['user__username']
        unique_together = ('user', 'avatar')

    def __str__(self):
        return f'{self.user.username} 的个人资料'
    
    def save(self, *args, **kwargs):
        # 处理头像上传和压缩
        if self.avatar and hasattr(self.avatar, 'file'):
            try:
                # 打开图片
                img = Image.open(self.avatar.file)
                
                # 如果图片大于300x300，将其调整为300x300
                if img.height > 300 or img.width > 300:
                    output_size = (300, 300)
                    img.thumbnail(output_size, Image.Resampling.LANCZOS)
                    
                    # 保存压缩后的图片到内存
                    img_io = io.BytesIO()
                    img_format = img.format if img.format else 'JPEG'
                    img.save(img_io, format=img_format, quality=85)
                    img_io.seek(0)
                    
                    # 创建新的文件对象
                    new_file = ContentFile(img_io.getvalue())
                    new_file.name = self.avatar.name
                    
                    # 替换原文件
                    self.avatar.file = new_file
                    
            except Exception as e:
                print(f"处理头像时出错: {str(e)}")
                # 如果处理失败，继续保存原文件
                pass
        
        super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        # 创建新用户档案，不设置默认头像
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    # 确保用户有档案，但不强制保存（避免触发头像访问）
    try:
        if hasattr(instance, 'profile'):
            # 只有在档案确实存在且需要更新时才保存
            pass
    except Profile.DoesNotExist:
        # 如果档案不存在，创建一个
        Profile.objects.create(user=instance)