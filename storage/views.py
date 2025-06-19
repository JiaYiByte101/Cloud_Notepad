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
from .models import CloudBackupRecord
from notebooks.models import Notebook, Category, Tag


@login_required
def storage_home(request):
    """存储页面首页"""
    cloud_backups = CloudBackupRecord.objects.filter(user=request.user).order_by('-created_at')
    
    try:
        from .backends.cloud import CloudBackupBackend
        cloud_backend = CloudBackupBackend()
        backup_stats = cloud_backend.get_storage_usage(request.user)
    except Exception:
        backup_stats = {
            'cloud_backup_count': cloud_backups.count(),
            'total_backup_size': sum(backup.file_size for backup in cloud_backups),
            'latest_backup': cloud_backups.first().created_at if cloud_backups.exists() else None,
        }

    context = {
        'cloud_backups': cloud_backups,
        'backup_stats': backup_stats,
    }
    return render(request, 'storage/home.html', context)


@login_required
def create_cloud_backup(request):
    """创建云版本备份"""
    if request.method == 'POST':
        try:
            from .backends.cloud import CloudBackupBackend
            
            cloud_backend = CloudBackupBackend()
            
            # 创建云版本备份
            backup_result = cloud_backend.create_version_backup(request.user)
            
            if backup_result['success']:
                # 创建云备份记录
                cloud_backup = CloudBackupRecord.objects.create(
                    user=request.user,
                    cloud_path=backup_result['cloud_path'],
                    cloud_url=backup_result['cloud_url'],
                    file_size=backup_result['file_size'],
                    notebook_count=backup_result['notebook_count'],
                )
                
                messages.success(request, f'成功创建云版本备份，共 {cloud_backup.notebook_count} 个笔记。')
            else:
                messages.error(request, f'云版本备份失败：{backup_result["error"]}')
                
        except Exception as e:
            messages.error(request, f'云版本备份失败：{str(e)}')

    return redirect('storage:home')


@login_required
def delete_cloud_backup(request, backup_id):
    """删除云版本备份"""
    if request.method == 'POST':
        try:
            cloud_backup = CloudBackupRecord.objects.get(id=backup_id, user=request.user)
            
            # 从云端删除文件
            from .backends.cloud import CloudBackupBackend
            cloud_backend = CloudBackupBackend()
            
            if cloud_backend.delete_cloud_backup(cloud_backup.cloud_path):
                # 删除记录
                cloud_backup.delete()
                messages.success(request, '云版本备份已成功删除。')
            else:
                messages.error(request, '删除云备份文件失败，但记录已删除。')
                cloud_backup.delete()
                
        except CloudBackupRecord.DoesNotExist:
            messages.error(request, '云版本备份记录不存在。')
        except Exception as e:
            messages.error(request, f'删除云版本备份失败：{str(e)}')

    return redirect('storage:home')


@login_required
def restore_cloud_backup(request, backup_id):
    """从云版本备份中选择性恢复数据"""
    if request.method == 'POST':
        try:
            cloud_backup = CloudBackupRecord.objects.get(id=backup_id, user=request.user)
            
            # 使用新的选择性恢复逻辑
            from .backends.cloud import CloudBackupBackend
            cloud_backend = CloudBackupBackend()
            
            restore_result = cloud_backend.restore_version_backup(request.user, cloud_backup.cloud_path)
            
            if restore_result['success']:
                restored_count = restore_result['restored_count']
                updated_count = restore_result['updated_count']
                
                if restored_count > 0 and updated_count > 0:
                    messages.success(request, f'版本恢复完成！新建了 {restored_count} 个笔记，更新了 {updated_count} 个笔记。')
                elif restored_count > 0:
                    messages.success(request, f'版本恢复完成！新建了 {restored_count} 个笔记。')
                elif updated_count > 0:
                    messages.success(request, f'版本恢复完成！更新了 {updated_count} 个笔记。')
                else:
                    messages.info(request, '版本恢复完成，但没有发现需要处理的笔记。')
            else:
                messages.error(request, f'版本恢复失败：{restore_result["error"]}')

        except CloudBackupRecord.DoesNotExist:
            messages.error(request, '云版本备份记录不存在。')
        except Exception as e:
            messages.error(request, f'恢复云版本备份失败：{str(e)}')

    return redirect('storage:home')


@login_required
def download_cloud_backup(request, backup_id):
    """下载云版本备份文件"""
    try:
        cloud_backup = CloudBackupRecord.objects.get(id=backup_id, user=request.user)
        
        # 重定向到云端URL
        return redirect(cloud_backup.cloud_url)
        
    except CloudBackupRecord.DoesNotExist:
        messages.error(request, '云版本备份记录不存在。')
    
    return redirect('storage:home')

