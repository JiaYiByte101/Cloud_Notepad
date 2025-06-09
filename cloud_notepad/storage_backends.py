from qcloud_cos import CosConfig, CosS3Client
from django.core.files.storage import Storage
from django.core.files.base import ContentFile
from django.conf import settings
from django.utils.deconstruct import deconstructible
import uuid
import os
import logging

logger = logging.getLogger(__name__)

@deconstructible
class TencentCOSStorage(Storage):
    def __init__(self):
        try:
            config = CosConfig(
                Region=settings.COS_REGION,
                SecretId=settings.COS_SECRET_ID,
                SecretKey=settings.COS_SECRET_KEY,
                Token=None,
                Scheme='https'
            )
            self.client = CosS3Client(config)
            self.bucket = settings.COS_BUCKET_NAME
            logger.info(f"腾讯云COS存储初始化成功，Bucket: {self.bucket}")
        except Exception as e:
            logger.error(f"腾讯云COS存储初始化失败: {str(e)}")
            raise

    def _save(self, name, content):
        """保存文件到腾讯云COS"""
        try:
            # 确保内容指针在开始位置
            if hasattr(content, 'seek'):
                content.seek(0)
            
            # 读取文件内容
            file_content = content.read()
            
            # 上传到COS
            self.client.put_object(
                Bucket=self.bucket,
                Body=file_content,
                Key=name,
                EnableMD5=False
            )
            
            logger.info(f"文件上传成功: {name}")
            return name
            
        except Exception as e:
            logger.error(f"文件上传失败 {name}: {str(e)}")
            raise

    def _open(self, name, mode='rb'):
        """从腾讯云COS打开文件"""
        try:
            response = self.client.get_object(
                Bucket=self.bucket,
                Key=name
            )
            return ContentFile(response['Body'].read())
        except Exception as e:
            logger.error(f"文件打开失败 {name}: {str(e)}")
            raise

    def exists(self, name):
        """检查文件是否存在"""
        try:
            self.client.head_object(
                Bucket=self.bucket,
                Key=name
            )
            return True
        except Exception:
            return False

    def url(self, name):
        """获取文件的访问URL"""
        # 确保返回完整的腾讯云COS URL
        if name.startswith('http'):
            return name
        return f"{settings.COS_DOMAIN}/{name}"

    def delete(self, name):
        """删除文件"""
        try:
            self.client.delete_object(
                Bucket=self.bucket,
                Key=name
            )
            logger.info(f"文件删除成功: {name}")
        except Exception as e:
            logger.error(f"文件删除失败 {name}: {str(e)}")
            raise

    def size(self, name):
        """获取文件大小"""
        try:
            response = self.client.head_object(
                Bucket=self.bucket,
                Key=name
            )
            return int(response['Content-Length'])
        except Exception as e:
            logger.error(f"获取文件大小失败 {name}: {str(e)}")
            return 0

    def get_modified_time(self, name):
        """获取文件修改时间"""
        try:
            response = self.client.head_object(
                Bucket=self.bucket,
                Key=name
            )
            from datetime import datetime
            return datetime.strptime(response['Last-Modified'], '%a, %d %b %Y %H:%M:%S %Z')
        except Exception as e:
            logger.error(f"获取文件修改时间失败 {name}: {str(e)}")
            return None

    def path(self, name):
        """
        COS存储不支持本地路径，但为了兼容性，我们返回一个虚拟路径
        注意：这个路径不能用于实际的文件操作
        """
        # 对于云存储，我们不能提供真实的本地路径
        # 但某些Django组件可能会调用这个方法，所以我们返回一个标识性的路径
        return f"cos://{self.bucket}/{name}"

    def get_available_name(self, name, max_length=None):
        """
        获取可用的文件名，如果文件已存在则生成新的文件名
        """
        if self.exists(name):
            # 如果文件已存在，生成新的文件名
            import uuid
            file_name, file_ext = os.path.splitext(name)
            name = f"{file_name}_{uuid.uuid4().hex[:8]}{file_ext}"
        return name

    def listdir(self, path):
        """
        列出目录内容（可选实现）
        """
        try:
            response = self.client.list_objects(
                Bucket=self.bucket,
                Prefix=path,
                Delimiter='/'
            )
            
            directories = []
            files = []
            
            # 处理目录
            if 'CommonPrefixes' in response:
                for prefix in response['CommonPrefixes']:
                    dir_name = prefix['Prefix'].rstrip('/').split('/')[-1]
                    directories.append(dir_name)
            
            # 处理文件
            if 'Contents' in response:
                for obj in response['Contents']:
                    if not obj['Key'].endswith('/'):  # 不是目录
                        file_name = obj['Key'].split('/')[-1]
                        if file_name:  # 确保不是空字符串
                            files.append(file_name)
            
            return directories, files
            
        except Exception as e:
            logger.error(f"列出目录失败 {path}: {str(e)}")
            return [], []

