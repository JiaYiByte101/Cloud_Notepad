# accounts/models.py

from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from PIL import Image
import os

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(default='user_dark.png', upload_to='profile_pics')

    def __str__(self):
        return f'{self.user.username} 的个人资料'
    
    def save(self, *args, **kwargs):
        # 如果是默认头像且文件不存在，从静态目录复制
        if self.avatar.name == 'user_dark.png' and not os.path.exists(self.avatar.path):
            from django.conf import settings
            import shutil
            static_default = os.path.join(settings.STATIC_ROOT, 'img', 'user_dark.png')
            if os.path.exists(static_default):
                # 确保media目录存在
                media_dir = os.path.dirname(self.avatar.path)
                os.makedirs(media_dir, exist_ok=True)
                # 复制默认头像到media目录
                shutil.copy(static_default, self.avatar.path)
        
        super().save(*args, **kwargs)
        
        try:
            if self.avatar and os.path.exists(self.avatar.path):
                img = Image.open(self.avatar.path)
                
                # 如果图片大于300x300，将其调整为300x300
                if img.height > 300 or img.width > 300:
                    output_size = (300, 300)
                    img.thumbnail(output_size)
                    img.save(self.avatar.path)
        except Exception as e:
            print(f"处理头像时出错: {str(e)}")
            # 如果处理失败，设置为默认头像
            self.avatar = 'user_dark.png'
            super().save(*args, **kwargs)


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save()