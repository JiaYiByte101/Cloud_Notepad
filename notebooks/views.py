# notebooks/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Notebook, Category, Tag
from .forms import NotebookForm, CategoryForm, TagForm, CollaborationNotebookForm
from django.http import JsonResponse, HttpResponseRedirect, HttpResponse
import json
import os
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import datetime
from django.template.loader import render_to_string
from django.utils.text import slugify
from io import BytesIO
from xhtml2pdf import pisa
from html import unescape
import re


@login_required
def notebook_list(request):
    """显示用户的笔记列表"""
    category_id = request.GET.get('category')
    tag_id = request.GET.get('tag')
    search_query = request.GET.get('search')

    notebooks = Notebook.objects.filter(user=request.user)

    # 根据分类筛选
    if category_id:
        notebooks = notebooks.filter(category_id=category_id)

    # 根据标签筛选
    if tag_id:
        notebooks = notebooks.filter(tags__id=tag_id)

    # 根据搜索关键词筛选
    if search_query:
        notebooks = notebooks.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query)
        )

    # 获取用户的所有分类和标签，用于侧边栏
    categories = Category.objects.filter(user=request.user)
    tags = Tag.objects.filter(user=request.user)

    context = {
        'notebooks': notebooks,
        'categories': categories,
        'tags': tags,
        'selected_category': category_id,
        'selected_tag': tag_id,
        'search_query': search_query
    }
    return render(request, 'notebooks/notebook_list.html', context)


@login_required
def notebook_detail(request, notebook_id):
    """查看单个笔记详情"""
    # 同时检查是否是笔记所有者或是协作项目成员
    notebook = get_object_or_404(Notebook, id=notebook_id)
    
    # 检查权限 - 所有者可以直接查看
    if notebook.user == request.user:
        has_edit_permission = True
    else:
        # 检查是否是协作项目的成员
        has_view_permission = False
        has_edit_permission = False
        
        # 检查用户是否是协作项目的成员
        for project in notebook.collaboration_projects.all():
            # 项目创建者有编辑权限
            if project.owner == request.user:
                has_view_permission = True
                has_edit_permission = True
                break
            
            # 检查成员权限
            membership = project.members.filter(user=request.user, status='accepted').first()
            if membership:
                has_view_permission = True
                # 编辑者有编辑权限
                if membership.role == 'editor':
                    has_edit_permission = True
                break
        
        # 没有任何权限则不允许查看
        if not has_view_permission:
            messages.error(request, '您没有权限查看此笔记')
            return redirect('notebooks:list')
    
    context = {
        'notebook': notebook,
        'has_edit_permission': has_edit_permission
    }
    return render(request, 'notebooks/notebook_detail.html', context)


@login_required
def notebook_create(request):
    """创建新笔记"""
    if request.method == 'POST':
        form = NotebookForm(request.POST, user=request.user)
        if form.is_valid():
            notebook = form.save(commit=False)
            notebook.user = request.user
            notebook.save()
            # 保存标签多对多关系
            form.save_m2m()
            messages.success(request, '笔记创建成功！')
            return redirect('notebooks:detail', notebook_id=notebook.id)
    else:
        form = NotebookForm(user=request.user)  # 确保传递用户参数

    return render(request, 'notebooks/notebook_form.html', {
        'form': form,
        'title': '创建新笔记'
    })


@login_required
def notebook_edit(request, notebook_id):
    """编辑笔记"""
    notebook = get_object_or_404(Notebook, id=notebook_id)
    
    # 检查编辑权限
    has_edit_permission = False
    
    # 笔记所有者有编辑权限
    if notebook.user == request.user:
        has_edit_permission = True
    else:
        # 检查协作项目中的权限
        for project in notebook.collaboration_projects.all():
            # 项目创建者有编辑权限
            if project.owner == request.user:
                has_edit_permission = True
                break
            
            # 编辑者角色有编辑权限
            membership = project.members.filter(user=request.user, status='accepted', role='editor').first()
            if membership:
                has_edit_permission = True
                break
    
    # 没有编辑权限则重定向
    if not has_edit_permission:
        messages.error(request, '您没有权限编辑此笔记')
        return redirect('notebooks:detail', notebook_id=notebook.id)
    
    # 如果是协作项目中的笔记，检查是否有编辑锁
    if notebook.collaboration_projects.exists():
        from collaboration.models import CollaborationLock
        from django.utils import timezone
        
        # 清理过期锁
        CollaborationLock.objects.filter(
            notebook=notebook,
            expires_at__lt=timezone.now()
        ).delete()
        
        # 检查当前用户是否有锁
        user_lock = CollaborationLock.objects.filter(
            notebook=notebook, 
            user=request.user
        ).first()
        
        if not user_lock:
            messages.error(request, '您需要先获取编辑锁才能编辑此笔记')
            return redirect('notebooks:detail', notebook_id=notebook.id)
        
        # 检查是否有其他用户的锁
        other_locks = CollaborationLock.objects.filter(notebook=notebook).exclude(user=request.user)
        if other_locks.exists():
            other_lock = other_locks.first()
            messages.error(request, f'此笔记当前被 {other_lock.user.username} 锁定')
            return redirect('notebooks:detail', notebook_id=notebook.id)
    
    # 处理表单提交
    if request.method == 'POST':
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"编辑笔记 {notebook_id}, 是否为协作笔记: {notebook.collaboration_projects.exists()}")
        logger.info(f"POST数据: {dict(request.POST)}")
        # 如果是协作项目中的笔记，需要验证锁
        if notebook.collaboration_projects.exists():
            from collaboration.models import CollaborationLock
            from django.utils import timezone
            
            # 检查当前用户是否持有有效的锁
            try:
                lock = CollaborationLock.objects.filter(
                    notebook=notebook, 
                    user=request.user
                ).latest('locked_at')
                
                if lock.is_expired():
                    # 锁已过期
                    lock.delete()
                    messages.error(request, '编辑锁已过期，请重新获取编辑权限')
                    return redirect('notebooks:detail', notebook_id=notebook.id)
                    
            except CollaborationLock.DoesNotExist:
                # 用户没有锁
                messages.error(request, '您没有编辑锁，无法保存修改')
                return redirect('notebooks:detail', notebook_id=notebook.id)
            
            # 检查是否有其他用户的锁（双重保险）
            other_locks = CollaborationLock.objects.filter(
                notebook=notebook
            ).exclude(user=request.user)
            
            for other_lock in other_locks:
                if not other_lock.is_expired():
                    messages.error(request, f'此笔记当前被 {other_lock.user.username} 锁定，无法保存')
                    return redirect('notebooks:detail', notebook_id=notebook.id)
                else:
                    # 清理过期的锁
                    other_lock.delete()
        
        # 判断是否是协作笔记，选择相应的表单
        is_collaboration = notebook.collaboration_projects.exists()
        
        if is_collaboration:
            form = CollaborationNotebookForm(request.POST, instance=notebook, user=notebook.user)
            logger.info("使用CollaborationNotebookForm")
        else:
            form = NotebookForm(request.POST, instance=notebook, user=notebook.user)
            logger.info("使用NotebookForm")
            
        if form.is_valid():
            logger.info("表单验证通过")
            form.save()
            
            # 如果是协作笔记，需要创建修改记录并发送群聊消息
            if is_collaboration:
                from collaboration.models import CollaborationEdit
                from friends.models import GroupMessage
                
                # 获取修改大纲
                edit_summary = form.cleaned_data.get('edit_summary')
                logger.info(f"修改大纲: {edit_summary}")
                
                # 为每个关联的协作项目创建修改记录和发送群聊消息
                for project in notebook.collaboration_projects.all():
                    # 创建修改记录
                    edit_record = CollaborationEdit.objects.create(
                        project=project,
                        notebook=notebook,
                        editor=request.user,
                        summary=edit_summary
                    )
                    
                    # 如果项目有群聊，发送通知消息
                    if hasattr(project, 'chat_group') and project.chat_group:
                        notification_message = edit_record.get_notification_message()
                        GroupMessage.objects.create(
                            group=project.chat_group,
                            sender=request.user,
                            content=notification_message,
                            message_type='notification'
                        )
                        logger.info(f"已发送群聊通知: {notification_message}")
                
                # 释放编辑锁
                CollaborationLock.objects.filter(
                    notebook=notebook, 
                    user=request.user
                ).delete()
            
            messages.success(request, '笔记更新成功！')
            return redirect('notebooks:detail', notebook_id=notebook.id)
        else:
            # 表单验证失败
            logger.error(f"表单验证失败: {form.errors}")
            logger.error(f"表单数据: {form.data}")
            logger.error(f"表单cleaned_data: {getattr(form, 'cleaned_data', '无')}")
            if is_collaboration and 'edit_summary' in form.errors:
                messages.error(request, '请填写修改大纲！')
            else:
                messages.error(request, f'表单验证失败: {form.errors}')
    else:
        # 判断是否是协作笔记，选择相应的表单
        is_collaboration = notebook.collaboration_projects.exists()
        
        if is_collaboration:
            form = CollaborationNotebookForm(instance=notebook, user=notebook.user)
        else:
            form = NotebookForm(instance=notebook, user=notebook.user)

    return render(request, 'notebooks/notebook_form.html', {
        'form': form,
        'notebook': notebook,
        'title': '编辑笔记',
        'is_collaboration': notebook.collaboration_projects.exists()
    })


@login_required
def notebook_cancel_edit(request, notebook_id):
    """取消编辑笔记，释放协作锁"""
    notebook = get_object_or_404(Notebook, id=notebook_id)
    
    # 检查用户是否有权限访问此笔记
    has_access = False
    
    # 检查是否是笔记所有者
    if notebook.user == request.user:
        has_access = True
    
    # 检查是否是协作项目成员
    if not has_access:
        for project in notebook.collaboration_projects.all():
            if project.members.filter(user=request.user, status='accepted').exists():
                has_access = True
                break
    
    if not has_access:
        if request.method == 'POST':
            # 对于sendBeacon请求，返回简单的HTTP响应
            from django.http import HttpResponse
            return HttpResponse('Unauthorized', status=403)
        messages.error(request, '您没有权限访问此笔记')
        return redirect('notebooks:list')
    
    # 如果是协作笔记，释放当前用户的编辑锁
    if notebook.collaboration_projects.exists():
        from collaboration.models import CollaborationLock
        
        # 删除当前用户的锁
        deleted_count = CollaborationLock.objects.filter(
            notebook=notebook, 
            user=request.user
        ).delete()[0]
        
        if request.method == 'POST':
            # 对于sendBeacon请求，返回简单的HTTP响应
            from django.http import HttpResponse
            return HttpResponse('OK' if deleted_count > 0 else 'No lock found')
        
        if deleted_count > 0:
            messages.success(request, '已取消编辑并释放编辑锁')
        else:
            messages.info(request, '已取消编辑')
    else:
        if request.method == 'POST':
            # 对于sendBeacon请求，返回简单的HTTP响应
            from django.http import HttpResponse
            return HttpResponse('OK')
        messages.info(request, '已取消编辑')
    
    # 重定向到笔记详情页面
    return redirect('notebooks:detail', notebook_id=notebook.id)


@login_required
def notebook_delete(request, notebook_id):
    """删除笔记"""
    notebook = get_object_or_404(Notebook, id=notebook_id, user=request.user)

    if request.method == 'POST':
        notebook.delete()
        messages.success(request, '笔记已删除！')
        return redirect('notebooks:list')

    return render(request, 'notebooks/notebook_confirm_delete.html', {'notebook': notebook})


@login_required
def category_list(request):
    """显示用户的分类列表"""
    categories = Category.objects.filter(user=request.user)
    return render(request, 'notebooks/category_list.html', {'categories': categories})


@login_required
def tag_list(request):
    """显示用户的标签列表"""
    tags = Tag.objects.filter(user=request.user)
    return render(request, 'notebooks/tag_list.html', {'tags': tags})


@login_required
def create_category(request):
    """创建新分类"""
    if request.method == 'POST':
        name = request.POST.get('name')
        parent_id = request.POST.get('parent')

        if name:
            try:
                parent = None
                if parent_id:
                    parent = get_object_or_404(Category, id=parent_id, user=request.user)

                Category.objects.create(
                    name=name,
                    user=request.user,
                    parent=parent
                )
                messages.success(request, '分类创建成功！')
            except Exception as e:
                messages.error(request, f'分类创建失败：{str(e)}')
        else:
            messages.error(request, '分类名称不能为空。')

    return redirect('notebooks:categories')


@login_required
def edit_category(request):
    """编辑分类"""
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        category = get_object_or_404(Category, id=category_id, user=request.user)

        form = CategoryForm(request.POST, instance=category, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '分类更新成功！')
        else:
            messages.error(request, '分类更新失败，请检查输入。')
    return redirect('notebooks:categories')


@login_required
def delete_category(request):
    """删除分类"""
    if request.method == 'POST':
        category_id = request.POST.get('category_id')
        category = get_object_or_404(Category, id=category_id, user=request.user)

        if Notebook.objects.filter(category=category).exists():
            Notebook.objects.filter(category=category).update(category=None)

        category.delete()
        messages.success(request, '分类已删除！')
    return redirect('notebooks:categories')


@login_required
def create_tag(request):
    """创建新标签"""
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            tag = form.save(commit=False)
            tag.user = request.user

            if Tag.objects.filter(name=tag.name, user=request.user).exists():
                messages.error(request, f'标签 "{tag.name}" 已存在！')
            else:
                tag.save()
                messages.success(request, '标签创建成功！')
        else:
            messages.error(request, '标签创建失败，请检查输入。')
    return redirect('notebooks:tags')


@login_required
def edit_tag(request):
    """编辑标签"""
    if request.method == 'POST':
        tag_id = request.POST.get('tag_id')
        tag = get_object_or_404(Tag, id=tag_id, user=request.user)

        form = TagForm(request.POST, instance=tag)
        if form.is_valid():
            new_name = form.cleaned_data['name']
            if new_name != tag.name and Tag.objects.filter(name=new_name, user=request.user).exists():
                messages.error(request, f'标签 "{new_name}" 已存在！')
            else:
                form.save()
                messages.success(request, '标签更新成功！')
        else:
            messages.error(request, '标签更新失败，请检查输入。')
    return redirect('notebooks:tags')


@login_required
def delete_tag(request):
    """删除标签"""
    if request.method == 'POST':
        tag_id = request.POST.get('tag_id')
        tag = get_object_or_404(Tag, id=tag_id, user=request.user)

        tag.delete()
        messages.success(request, '标签已删除！')
    return redirect('notebooks:tags')


@login_required
@csrf_exempt
def upload_file(request):
    """处理TinyMCE编辑器中的文件上传（图片、视频和音频）"""
    if request.method == 'POST':
        file_obj = request.FILES.get('file')
        if file_obj:
            # 获取文件扩展名
            file_extension = os.path.splitext(file_obj.name)[1].lower()
            
            # 定义允许的文件类型
            allowed_image_types = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
            allowed_video_types = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv']
            allowed_audio_types = ['.mp3', '.wav', '.ogg', '.aac', '.flac', '.m4a']
            
            all_allowed_types = allowed_image_types + allowed_video_types + allowed_audio_types
            
            # 检查文件类型
            if file_extension not in all_allowed_types:
                return JsonResponse({
                    'error': f'不支持的文件类型。支持的格式：{", ".join(all_allowed_types)}'
                }, status=400)
            
            # 检查文件大小（图片最大10MB，视频最大100MB，音频最大50MB）
            max_size = 10 * 1024 * 1024  # 默认10MB
            if file_extension in allowed_video_types:
                max_size = 100 * 1024 * 1024  # 视频100MB
            elif file_extension in allowed_audio_types:
                max_size = 50 * 1024 * 1024   # 音频50MB
                
            if file_obj.size > max_size:
                size_mb = max_size / (1024 * 1024)
                return JsonResponse({
                    'error': f'文件大小超过限制（最大 {size_mb}MB）'
                }, status=400)
            
            try:
                # 使用Django的存储系统保存文件
                from django.core.files.storage import default_storage
                import uuid
                
                # 创建文件路径
                today = datetime.datetime.now().strftime('%Y%m%d')
                
                # 根据文件类型创建不同的子目录
                if file_extension in allowed_image_types:
                    sub_dir = 'images'
                elif file_extension in allowed_video_types:
                    sub_dir = 'videos'
                else:
                    sub_dir = 'audios'
                
                # 生成唯一文件名避免冲突
                file_name, file_ext = os.path.splitext(file_obj.name)
                unique_filename = f"{file_name}_{uuid.uuid4().hex[:8]}{file_ext}"
                
                # 构建存储路径
                storage_path = f"uploads/{request.user.username}/{today}/{sub_dir}/{unique_filename}"
                
                # 使用默认存储系统保存文件（会自动使用腾讯云COS）
                saved_path = default_storage.save(storage_path, file_obj)
                
                # 获取文件URL
                file_url = default_storage.url(saved_path)
                
                # 根据文件类型返回不同的响应
                response_data = {'location': file_url}
                
                # 为视频和音频添加额外信息
                if file_extension in allowed_video_types:
                    response_data['file_type'] = 'video'
                    response_data['mime_type'] = f'video/{file_extension[1:]}'
                elif file_extension in allowed_audio_types:
                    response_data['file_type'] = 'audio'
                    response_data['mime_type'] = f'audio/{file_extension[1:]}'
                else:
                    response_data['file_type'] = 'image'
                
                return JsonResponse(response_data)
                
            except Exception as e:
                import logging
                logger = logging.getLogger('notebooks')
                logger.error(f"文件上传到云存储失败: {str(e)}")
                return JsonResponse({'error': f'文件上传失败: {str(e)}'}, status=500)
            
    # 上传失败
    return JsonResponse({'error': '文件上传失败'}, status=400)


@login_required
def media_preview(request, file_path):
    """媒体文件预览视图"""
    import mimetypes
    from django.http import FileResponse, Http404
    
    # 构建完整的文件路径
    full_path = os.path.join(settings.MEDIA_ROOT, file_path)
    
    # 检查文件是否存在
    if not os.path.exists(full_path):
        raise Http404("文件不存在")
    
    # 检查文件是否属于当前用户（安全检查）
    if request.user.username not in file_path:
        raise Http404("无权访问此文件")
    
    # 获取文件的 MIME 类型
    mime_type, _ = mimetypes.guess_type(full_path)
    
    try:
        # 返回文件响应
        response = FileResponse(
            open(full_path, 'rb'),
            content_type=mime_type,
            as_attachment=False  # 设置为 False 以便在浏览器中预览
        )
        
        # 设置缓存头
        response['Cache-Control'] = 'public, max-age=3600'
        
        return response
    except Exception as e:
        raise Http404(f"文件读取错误: {str(e)}")


@login_required
def notebook_download_pdf(request, notebook_id):
    """下载笔记为PDF格式"""
    notebook = get_object_or_404(Notebook, id=notebook_id)
    
    # 验证权限：用户是笔记的拥有者或是关联项目的成员
    is_authorized = notebook.user == request.user
    
    # 如果不是拥有者，检查是否是项目成员
    if not is_authorized and notebook.collaboration_projects.exists():
        for project in notebook.collaboration_projects.all():
            if project.owner == request.user or project.members.filter(user=request.user, status='accepted').exists():
                is_authorized = True
                break
    
    if not is_authorized:
        messages.error(request, "您没有权限下载该笔记")
        return redirect('notebooks:list')
    
    # 生成HTML内容
    html_string = render_to_string('notebooks/notebook_pdf_template.html', {
        'notebook': notebook,
        'request': request
    })
    
    # 创建HTTP响应
    response = HttpResponse(content_type='application/pdf')
    # 处理文件名，确保中文字符正确显示
    safe_filename = notebook.title.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
    response['Content-Disposition'] = f'attachment; filename="{safe_filename}.pdf"'
    
    # 将CSS链接转换为绝对路径，确保在PDF中能正确加载样式
    base_url = request.build_absolute_uri('/')[:-1]  # 移除末尾的斜杠
    
    # 创建PDF
    buffer = BytesIO()
    
    # 使用专门的字体配置函数
    from .utils import prepare_pdf_html
    html_string = prepare_pdf_html(html_string)
    
    pisa_status = pisa.CreatePDF(
        html_string,
        dest=buffer,
        encoding='utf-8',
        link_callback=lambda uri, rel: os.path.join(base_url, uri) if uri.startswith('/') else uri
    )
    
    if pisa_status.err:
        return HttpResponse('PDF生成时出现错误', status=500)
    
    # 获取PDF内容
    pdf = buffer.getvalue()
    buffer.close()
    
    # 写入响应
    response.write(pdf)
    return response


@login_required
def notebook_download_html(request, notebook_id):
    """下载笔记为HTML格式"""
    notebook = get_object_or_404(Notebook, id=notebook_id)
    
    # 验证权限：用户是笔记的拥有者或是关联项目的成员
    is_authorized = notebook.user == request.user
    
    # 如果不是拥有者，检查是否是项目成员
    if not is_authorized and notebook.collaboration_projects.exists():
        for project in notebook.collaboration_projects.all():
            if project.owner == request.user or project.members.filter(user=request.user, status='accepted').exists():
                is_authorized = True
                break
    
    if not is_authorized:
        messages.error(request, "您没有权限下载该笔记")
        return redirect('notebooks:list')
    
    # 生成HTML内容
    html_string = render_to_string('notebooks/notebook_html_template.html', {
        'notebook': notebook
    })
    
    # 创建HTTP响应
    response = HttpResponse(content_type='text/html')
    # 处理文件名，确保中文字符正确显示
    safe_filename = notebook.title.replace('/', '_').replace('\\', '_').replace(':', '_').replace('*', '_').replace('?', '_').replace('"', '_').replace('<', '_').replace('>', '_').replace('|', '_')
    response['Content-Disposition'] = f'attachment; filename="{safe_filename}.html"'
    response.write(html_string)
    
    return response


@login_required
def ai_polish_text(request):
    """AI文本润色接口"""
    if request.method == 'POST':
        try:
            # 获取选中的文本
            selected_text = request.POST.get('text', '').strip()
            
            if not selected_text:
                return JsonResponse({
                    'success': False,
                    'error': '请先选中要润色的文本'
                })
            
            # 导入润色函数
            from .utils import polish_text
            
            # 调用AI润色
            polished_text = polish_text(selected_text)
            
            # 返回润色后的文本
            return JsonResponse({
                'success': True,
                'polished_text': polished_text,
                'original_text': selected_text
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'润色失败：{str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'error': '无效的请求方法'
    })

