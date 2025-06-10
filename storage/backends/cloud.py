import os
import json
import zipfile
import tempfile
from django.conf import settings
from django.core.files.storage import default_storage
from django.utils import timezone
from notebooks.models import Notebook, Category, Tag
import logging

logger = logging.getLogger(__name__)

class CloudBackupBackend:
    """云备份后端，专注于版本控制功能"""
    
    def __init__(self):
        self.storage = default_storage
    
    def create_version_backup(self, user):
        """
        创建用户数据的版本备份
        
        Args:
            user: 用户对象
        
        Returns:
            dict: 包含备份结果的字典
        """
        try:
            # 获取用户的所有数据
            notebooks = Notebook.objects.filter(user=user)
            categories = Category.objects.filter(user=user)
            tags = Tag.objects.filter(user=user)
            
            # 创建临时ZIP文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
                temp_path = temp_file.name
            
            # 创建ZIP文件
            with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 添加元数据
                metadata = {
                    'user': user.username,
                    'email': user.email,
                    'backup_date': timezone.now().isoformat(),
                    'notebook_count': notebooks.count(),
                    'version': '2.0',  # 新版本标识，支持UUID
                }
                zipf.writestr('metadata.json', json.dumps(metadata, indent=4, ensure_ascii=False))
                
                # 添加笔记数据（包含UUID）
                notebooks_data = []
                for notebook in notebooks:
                    notebook_data = {
                        'uuid': str(notebook.uuid),  # 使用UUID作为主要标识符
                        'id': notebook.id,  # 保留ID用于兼容性
                        'title': notebook.title,
                        'content': notebook.content,
                        'created_at': notebook.created_at.isoformat(),
                        'updated_at': notebook.updated_at.isoformat(),
                        'is_public': notebook.is_public,
                        'is_featured': notebook.is_featured,
                        'view_count': notebook.view_count,
                        'category': notebook.category.name if notebook.category else None,
                        'tags': [tag.name for tag in notebook.tags.all()],
                    }
                    notebooks_data.append(notebook_data)
                
                zipf.writestr('notebooks.json', json.dumps(notebooks_data, indent=4, ensure_ascii=False))
                
                # 添加分类数据
                categories_data = []
                for category in categories:
                    category_data = {
                        'id': category.id,
                        'name': category.name,
                        'parent': category.parent.name if category.parent else None,
                        'created_at': category.created_at.isoformat(),
                    }
                    categories_data.append(category_data)
                
                zipf.writestr('categories.json', json.dumps(categories_data, indent=4, ensure_ascii=False))
                
                # 添加标签数据
                tags_data = []
                for tag in tags:
                    tag_data = {
                        'id': tag.id,
                        'name': tag.name,
                        'created_at': tag.created_at.isoformat(),
                    }
                    tags_data.append(tag_data)

                zipf.writestr('tags.json', json.dumps(tags_data, indent=4, ensure_ascii=False))

            # 创建云端文件名
            timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
            cloud_filename = f'version_backup_{user.username}_{timestamp}.zip'
            cloud_path = f"backups/{user.id}/versions/{cloud_filename}"
            
            # 上传到云端
            with open(temp_path, 'rb') as f:
                saved_path = self.storage.save(cloud_path, f)
            
            # 获取云端URL和文件大小
            cloud_url = self.storage.url(saved_path)
            file_size = os.path.getsize(temp_path)
            
            # 清理临时文件
            os.unlink(temp_path)
            
            logger.info(f"云版本备份创建成功: {saved_path}")
            
            return {
                'success': True,
                'cloud_path': saved_path,
                'cloud_url': cloud_url,
                'file_size': file_size,
                'notebook_count': notebooks.count(),
                'backup_filename': cloud_filename
            }
            
        except Exception as e:
            logger.error(f"云版本备份创建失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def restore_version_backup(self, user, cloud_path):
        """
        从云版本备份中选择性恢复数据
        基于UUID匹配：存在于版本文件中的笔记恢复到版本状态，不存在的笔记保持不动
        
        Args:
            user: 用户对象
            cloud_path: 云端备份文件路径
        
        Returns:
            dict: 恢复结果
        """
        temp_path = None
        try:
            logger.info(f"开始恢复版本备份: {cloud_path}")
            
            # 检查云端文件是否存在
            if not self.storage.exists(cloud_path):
                logger.error(f"云端文件不存在: {cloud_path}")
                return {
                    'success': False,
                    'error': f'云端备份文件不存在: {cloud_path}'
                }
            
            # 下载到临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
                temp_path = temp_file.name
                
            # 从云端下载文件
            try:
                # 直接使用COS客户端下载文件，避免Django存储接口的问题
                response = self.storage.client.get_object(
                    Bucket=self.storage.bucket,
                    Key=cloud_path
                )
                
                # 将响应内容写入临时文件
                with open(temp_path, 'wb') as local_file:
                    body = response['Body']
                    
                    # 分块读取以避免内存问题
                    while True:
                        chunk = body.read(8192)  # 8KB chunks
                        if not chunk:
                            break
                        local_file.write(chunk)
                
                # 验证下载的文件
                actual_size = os.path.getsize(temp_path)
                if actual_size == 0:
                    logger.error("下载的备份文件为空")
                    return {
                        'success': False,
                        'error': '下载的备份文件为空'
                    }
                    
            except Exception as download_error:
                logger.error(f"文件下载失败: {str(download_error)}")
                return {
                    'success': False,
                    'error': f'文件下载失败: {str(download_error)}'
                }
            
            # 验证ZIP文件
            try:
                with zipfile.ZipFile(temp_path, 'r') as test_zipf:
                    file_list = test_zipf.namelist()
                    
                    # 检查必要的文件是否存在
                    required_files = ['metadata.json', 'notebooks.json', 'categories.json', 'tags.json']
                    missing_files = [f for f in required_files if f not in file_list]
                    if missing_files:
                        logger.error(f"ZIP文件缺少必要文件: {missing_files}")
                        return {
                            'success': False,
                            'error': f'备份文件格式不完整，缺少: {", ".join(missing_files)}'
                        }
                        
            except zipfile.BadZipFile as zip_error:
                logger.error(f"ZIP文件格式错误: {str(zip_error)}")
                return {
                    'success': False,
                    'error': f'备份文件不是有效的ZIP格式: {str(zip_error)}'
                }
            except Exception as zip_error:
                logger.error(f"ZIP文件验证失败: {str(zip_error)}")
                return {
                    'success': False,
                    'error': f'备份文件验证失败: {str(zip_error)}'
                }
            
            # 解析备份文件
            with zipfile.ZipFile(temp_path, 'r') as zipf:
                # 检查版本
                metadata_json = zipf.read('metadata.json').decode('utf-8')
                metadata = json.loads(metadata_json)
                backup_version = metadata.get('version', '1.0')
                
                # 提取数据
                notebooks_json = zipf.read('notebooks.json').decode('utf-8')
                notebooks_data = json.loads(notebooks_json)

                categories_json = zipf.read('categories.json').decode('utf-8')
                categories_data = json.loads(categories_json)

                tags_json = zipf.read('tags.json').decode('utf-8')
                tags_data = json.loads(tags_json)

            # 清理临时文件
            if temp_path and os.path.exists(temp_path):
                os.unlink(temp_path)
                temp_path = None
            
            # 恢复分类
            category_map = {}  # 名称到对象的映射
            for cat_data in categories_data:
                if cat_data.get('parent') is None:
                    category, created = Category.objects.get_or_create(
                        user=user,
                        name=cat_data['name'],
                        defaults={'parent': None}
                    )
                    category_map[cat_data['name']] = category

            # 处理有parent的分类
            for cat_data in categories_data:
                if cat_data.get('parent') is not None:
                    parent_name = cat_data['parent']
                    if parent_name in category_map:
                        parent = category_map[parent_name]
                        category, created = Category.objects.get_or_create(
                            user=user,
                            name=cat_data['name'],
                            defaults={'parent': parent}
                        )
                        category_map[cat_data['name']] = category

            # 恢复标签
            tag_map = {}  # 名称到对象的映射
            for tag_data in tags_data:
                tag, created = Tag.objects.get_or_create(
                    user=user,
                    name=tag_data['name']
                )
                tag_map[tag_data['name']] = tag

            # 选择性恢复笔记
            restored_count = 0
            updated_count = 0
            
            for notebook_data in notebooks_data:
                # 获取分类
                category = None
                if notebook_data.get('category'):
                    category = category_map.get(notebook_data['category'])

                # 根据版本处理UUID
                if backup_version >= '2.0' and 'uuid' in notebook_data:
                    # 新版本：使用UUID查找
                    try:
                        existing_notebook = Notebook.objects.get(
                            user=user,
                            uuid=notebook_data['uuid']
                        )
                        # 更新现有笔记到版本状态
                        existing_notebook.title = notebook_data['title']
                        existing_notebook.content = notebook_data['content']
                        existing_notebook.category = category
                        existing_notebook.is_public = notebook_data.get('is_public', False)
                        existing_notebook.is_featured = notebook_data.get('is_featured', False)
                        existing_notebook.save()
                        
                        # 更新标签
                        existing_notebook.tags.clear()
                        for tag_name in notebook_data.get('tags', []):
                            if tag_name in tag_map:
                                existing_notebook.tags.add(tag_map[tag_name])
                        
                        updated_count += 1
                        
                    except Notebook.DoesNotExist:
                        # UUID不存在，创建新笔记
                        notebook = Notebook.objects.create(
                            uuid=notebook_data['uuid'],
                            title=notebook_data['title'],
                            content=notebook_data['content'],
                            user=user,
                            category=category,
                            is_public=notebook_data.get('is_public', False),
                            is_featured=notebook_data.get('is_featured', False),
                        )
                        
                        # 添加标签
                        for tag_name in notebook_data.get('tags', []):
                            if tag_name in tag_map:
                                notebook.tags.add(tag_map[tag_name])
                        
                        restored_count += 1
                else:
                    # 旧版本：使用标题查找（兼容性处理）
                    try:
                        existing_notebook = Notebook.objects.get(
                            user=user,
                            title=notebook_data['title']
                        )
                        # 更新现有笔记
                        existing_notebook.content = notebook_data['content']
                        existing_notebook.category = category
                        existing_notebook.is_public = notebook_data.get('is_public', False)
                        existing_notebook.save()
                        
                        # 更新标签
                        existing_notebook.tags.clear()
                        for tag_name in notebook_data.get('tags', []):
                            if tag_name in tag_map:
                                existing_notebook.tags.add(tag_map[tag_name])
                        
                        updated_count += 1
                        
                    except Notebook.DoesNotExist:
                        # 创建新笔记
                        notebook = Notebook.objects.create(
                            title=notebook_data['title'],
                            content=notebook_data['content'],
                            user=user,
                            category=category,
                            is_public=notebook_data.get('is_public', False),
                        )
                        
                        # 添加标签
                        for tag_name in notebook_data.get('tags', []):
                            if tag_name in tag_map:
                                notebook.tags.add(tag_map[tag_name])
                        
                        restored_count += 1

            logger.info(f"版本恢复完成: 新建 {restored_count} 个笔记，更新 {updated_count} 个笔记")
            
            return {
                'success': True,
                'restored_count': restored_count,
                'updated_count': updated_count,
                'total_processed': restored_count + updated_count
            }
            
        except Exception as e:
            logger.error(f"版本恢复失败: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
        finally:
            # 确保清理临时文件
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except:
                    pass
    
    def delete_cloud_backup(self, cloud_path):
        """
        删除云端备份文件
        
        Args:
            cloud_path: 云端文件路径
        
        Returns:
            bool: 删除是否成功
        """
        try:
            self.storage.delete(cloud_path)
            logger.info(f"云备份删除成功: {cloud_path}")
            return True
        except Exception as e:
            logger.error(f"云备份删除失败 {cloud_path}: {str(e)}")
            return False

    def get_storage_usage(self, user):
        """
        获取用户的存储使用情况
        
        Args:
            user: 用户对象
        
        Returns:
            dict: 存储使用情况统计
        """
        try:
            from ..models import CloudBackupRecord
            
            cloud_backups = CloudBackupRecord.objects.filter(user=user)
            
            return {
                'cloud_backup_count': cloud_backups.count(),
                'total_backup_size': sum(backup.file_size for backup in cloud_backups),
                'latest_backup': cloud_backups.first().created_at if cloud_backups.exists() else None,
            }
        except Exception as e:
            logger.error(f"获取存储使用情况失败: {str(e)}")
            return {
                'cloud_backup_count': 0,
                'total_backup_size': 0,
                'latest_backup': None,
            }
