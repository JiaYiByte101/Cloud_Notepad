# storage/views.py

import os
import json
import datetime
import zipfile
import tempfile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.conf import settings
from django.utils import timezone
from .models import BackupRecord, SyncStatus
from notebooks.models import Notebook, Category, Tag
import time


@login_required
def storage_home(request):
    """存储页面首页"""
    # 获取用户的备份记录
    backups = BackupRecord.objects.filter(user=request.user).order_by('-created_at')

    # 获取同步状态
    sync_status, created = SyncStatus.objects.get_or_create(user=request.user)

    context = {
        'backups': backups,
        'sync_status': sync_status,
    }
    return render(request, 'storage/home.html', context)


@login_required
def backup(request):
    """创建备份"""
    if request.method == 'POST':
        try:
            # 获取用户的所有笔记
            notebooks = Notebook.objects.filter(user=request.user)
            notebook_count = notebooks.count()

            if notebook_count == 0:
                messages.warning(request, '您没有任何笔记可以备份。')
                return redirect('storage:home')

            # 创建临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
                temp_path = temp_file.name

            # 创建ZIP文件
            with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 添加元数据
                metadata = {
                    'user': request.user.username,
                    'email': request.user.email,
                    'backup_date': timezone.now().isoformat(),
                    'notebook_count': notebook_count,
                }
                zipf.writestr('metadata.json', json.dumps(metadata, indent=4))

                # 添加笔记数据
                notebooks_data = []
                for notebook in notebooks:
                    notebook_data = {
                        'id': notebook.id,
                        'title': notebook.title,
                        'content': notebook.content,
                        'created_at': notebook.created_at.isoformat(),
                        'updated_at': notebook.updated_at.isoformat(),
                        'is_public': notebook.is_public,
                        'category': notebook.category.name if notebook.category else None,
                        'tags': [tag.name for tag in notebook.tags.all()],
                    }
                    notebooks_data.append(notebook_data)

                zipf.writestr('notebooks.json', json.dumps(notebooks_data, indent=4))

                # 添加分类和标签数据
                categories = Category.objects.filter(user=request.user)
                categories_data = [{'id': cat.id, 'name': cat.name, 'parent': cat.parent_id} for cat in categories]
                zipf.writestr('categories.json', json.dumps(categories_data, indent=4))

                tags = Tag.objects.filter(user=request.user)
                tags_data = [{'id': tag.id, 'name': tag.name} for tag in tags]
                zipf.writestr('tags.json', json.dumps(tags_data, indent=4))

            # 获取文件大小
            file_size = os.path.getsize(temp_path)

            # 创建目标目录（如果不存在）
            backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups', str(request.user.id))
            os.makedirs(backup_dir, exist_ok=True)

            # 创建备份文件名
            timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
            backup_filename = f'backup_{request.user.username}_{timestamp}.zip'
            backup_path = os.path.join(backup_dir, backup_filename)

            # 移动文件
            os.rename(temp_path, backup_path)

            # 创建备份记录
            backup_record = BackupRecord.objects.create(
                user=request.user,
                file_path=os.path.join('backups', str(request.user.id), backup_filename),
                file_size=file_size,
                notebook_count=notebook_count,
            )

            messages.success(request, f'成功创建备份，共 {notebook_count} 个笔记。')

        except Exception as e:
            messages.error(request, f'备份失败：{str(e)}')

        return redirect('storage:home')

    return redirect('storage:home')


@login_required
def download_backup(request, backup_id):
    """下载备份"""
    try:
        backup = BackupRecord.objects.get(id=backup_id, user=request.user)
        file_path = os.path.join(settings.MEDIA_ROOT, backup.file_path)

        if os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/zip')
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                return response
        else:
            messages.error(request, '备份文件不存在。')
    except BackupRecord.DoesNotExist:
        messages.error(request, '备份记录不存在。')

    return redirect('storage:home')


@login_required
def delete_backup(request, backup_id):
    """删除备份"""
    if request.method == 'POST':
        try:
            backup = BackupRecord.objects.get(id=backup_id, user=request.user)
            file_path = os.path.join(settings.MEDIA_ROOT, backup.file_path)

            # 删除文件
            if os.path.exists(file_path):
                os.remove(file_path)

            # 删除记录
            backup.delete()

            messages.success(request, '备份已成功删除。')
        except BackupRecord.DoesNotExist:
            messages.error(request, '备份记录不存在。')
        except Exception as e:
            messages.error(request, f'删除备份失败：{str(e)}')

    return redirect('storage:home')


@login_required
def sync_status(request):
    """获取同步状态"""
    sync_status, created = SyncStatus.objects.get_or_create(user=request.user)

    return JsonResponse({
        'last_sync': sync_status.last_sync.isoformat() if sync_status.last_sync else None,
        'is_syncing': sync_status.is_syncing,
        'sync_error': sync_status.sync_error,
    })


# storage/views.py 的剩余部分

@login_required
def sync_now(request):
    """执行同步操作"""
    if request.method == 'POST':
        sync_status, created = SyncStatus.objects.get_or_create(user=request.user)

        # 模拟同步过程（实际项目中这里应该调用真正的云存储API）
        try:
            sync_status.is_syncing = True
            sync_status.sync_error = ''
            sync_status.save()

            # 这里是模拟代码，实际项目中需要实现真正的云同步
            time.sleep(2)  # 模拟同步延迟

            # 更新同步状态
            sync_status.is_syncing = False
            sync_status.last_sync = timezone.now()
            sync_status.save()

            messages.success(request, '同步完成！所有数据已成功同步到云端。')
        except Exception as e:
            sync_status.is_syncing = False
            sync_status.sync_error = str(e)
            sync_status.save()
            messages.error(request, f'同步失败：{str(e)}')

    return redirect('storage:home')


@login_required
def restore_backup(request, backup_id):
    """从备份中恢复数据"""
    if request.method == 'POST':
        try:
            backup = BackupRecord.objects.get(id=backup_id, user=request.user)
            file_path = os.path.join(settings.MEDIA_ROOT, backup.file_path)

            if not os.path.exists(file_path):
                messages.error(request, '备份文件不存在。')
                return redirect('storage:home')

            # 解析备份文件
            with zipfile.ZipFile(file_path, 'r') as zipf:
                # 提取笔记数据
                notebooks_json = zipf.read('notebooks.json').decode('utf-8')
                notebooks_data = json.loads(notebooks_json)

                # 提取分类数据
                categories_json = zipf.read('categories.json').decode('utf-8')
                categories_data = json.loads(categories_json)

                # 提取标签数据
                tags_json = zipf.read('tags.json').decode('utf-8')
                tags_data = json.loads(tags_json)

            # 恢复分类
            category_map = {}  # 旧ID到新对象的映射
            for cat_data in categories_data:
                # 先创建没有parent的分类
                if cat_data['parent'] is None:
                    category, created = Category.objects.get_or_create(
                        user=request.user,
                        name=cat_data['name'],
                        defaults={'parent': None}
                    )
                    category_map[cat_data['id']] = category

            # 再处理有parent的分类
            for cat_data in categories_data:
                if cat_data['parent'] is not None:
                    if cat_data['parent'] in category_map:
                        parent = category_map[cat_data['parent']]
                        category, created = Category.objects.get_or_create(
                            user=request.user,
                            name=cat_data['name'],
                            defaults={'parent': parent}
                        )
                        category_map[cat_data['id']] = category

            # 恢复标签
            tag_map = {}  # 标签名到对象的映射
            for tag_data in tags_data:
                tag, created = Tag.objects.get_or_create(
                    user=request.user,
                    name=tag_data['name']
                )
                tag_map[tag_data['name']] = tag

            # 恢复笔记
            for notebook_data in notebooks_data:
                # 获取分类
                category = None
                if notebook_data['category']:
                    # 通过名称查找分类
                    try:
                        category = Category.objects.get(user=request.user, name=notebook_data['category'])
                    except Category.DoesNotExist:
                        pass

                # 创建笔记
                notebook, created = Notebook.objects.get_or_create(
                    user=request.user,
                    title=notebook_data['title'],
                    defaults={
                        'content': notebook_data['content'],
                        'category': category,
                        'is_public': notebook_data['is_public'],
                        'created_at': timezone.now(),
                        'updated_at': timezone.now(),
                    }
                )

                # 添加标签
                for tag_name in notebook_data['tags']:
                    if tag_name in tag_map:
                        notebook.tags.add(tag_map[tag_name])

            messages.success(request, f'成功从备份恢复了 {len(notebooks_data)} 个笔记。')

        except Exception as e:
            messages.error(request, f'恢复备份失败：{str(e)}')

    return redirect('storage:home')


@login_required
def cloud_storage(request):
    """云存储页面视图"""
    # 从session获取模拟的云存储文件列表
    cloud_files = request.session.get('cloud_files', [])
    
    # 模拟存储空间数据
    total_space = 1024  # 总空间（MB）
    # 简单模拟已用空间：每篇模拟笔记占用5MB
    used_space = len(cloud_files) * 5
    # 确保已用空间不超过总空间
    used_space = min(used_space, total_space)
    
    # 计算已用空间的百分比
    used_percentage = (used_space / total_space) * 100 if total_space > 0 else 0

    cloud_data = {
        'total_space': total_space,
        'used_space': used_space,
        'used_percentage': used_percentage,
        'files': cloud_files
    }
    return render(request, 'storage/cloud_storage.html', {'cloud_data': cloud_data})


@login_required
def save_to_cloud(request, notebook_id):
    """保存笔记到云存储"""
    notebook = get_object_or_404(Notebook, id=notebook_id, user=request.user)
    
    # 模拟云存储过程
    time.sleep(1)  # 模拟网络延迟
    
    # 获取或初始化session中的云存储文件列表
    cloud_files = request.session.get('cloud_files', [])
    
    # 检查是否已存在，避免重复添加（这里简单通过id判断，实际应有更复杂的唯一标识）
    if not any(f['id'] == notebook.id for f in cloud_files):
        # 模拟文件信息
        file_info = {
            'id': notebook.id,
            'name': notebook.title,
            'size': 5, # 模拟大小，单位MB
            'last_modified': time.strftime('%Y-%m-%d %H:%M'),
            'type': '笔记'
        }
        cloud_files.append(file_info)
        request.session['cloud_files'] = cloud_files
        messages.success(request, f'笔记 "{notebook.title}" 已成功保存到云存储！')
    else:
        messages.info(request, f'笔记 "{notebook.title}" 已存在于云存储中。')

    return redirect('notebooks:list')


@login_required
def sync_cloud(request):
    """同步云存储数据"""
    # 模拟同步过程
    time.sleep(2)  # 模拟网络延迟
    
    # 模拟成功同步
    messages.success(request, '云存储数据同步成功！')
    return JsonResponse({'status': 'success'})


@login_required
def delete_cloud_file(request):
    """模拟删除云存储中的文件"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            file_id_to_delete = data.get('file_id')
            
            if file_id_to_delete is not None:
                cloud_files = request.session.get('cloud_files', [])
                # 查找并移除对应的文件
                request.session['cloud_files'] = [f for f in cloud_files if f.get('id') != file_id_to_delete]
                # 标记session需要保存
                request.session.modified = True
                return JsonResponse({'status': 'success', 'message': '文件已移除'})
            else:
                return JsonResponse({'status': 'error', 'message': '无效的文件ID'}, status=400)
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': '无效的JSON数据'}, status=400)
    return JsonResponse({'status': 'error', 'message': '只允许POST请求'}, status=405)