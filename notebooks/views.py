# notebooks/views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Notebook, Category, Tag
from .forms import NotebookForm, CategoryForm, TagForm
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
    notebook = get_object_or_404(Notebook, id=notebook_id, user=request.user)
    return render(request, 'notebooks/notebook_detail.html', {'notebook': notebook})


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
    notebook = get_object_or_404(Notebook, id=notebook_id, user=request.user)

    if request.method == 'POST':
        form = NotebookForm(request.POST, instance=notebook, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, '笔记更新成功！')
            return redirect('notebooks:detail', notebook_id=notebook.id)
    else:
        form = NotebookForm(instance=notebook, user=request.user)

    return render(request, 'notebooks/notebook_form.html', {
        'form': form,
        'notebook': notebook,
        'title': '编辑笔记'
    })


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
    """处理TinyMCE编辑器中的文件上传（图片和视频）"""
    if request.method == 'POST':
        file_obj = request.FILES.get('file')
        if file_obj:
            # 创建存储目录
            today = datetime.datetime.now().strftime('%Y%m%d')
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', request.user.username, today)
            os.makedirs(upload_dir, exist_ok=True)
            
            # 保存文件
            file_path = os.path.join(upload_dir, file_obj.name)
            with open(file_path, 'wb+') as destination:
                for chunk in file_obj.chunks():
                    destination.write(chunk)
                    
            # 生成URL
            relative_path = os.path.join('uploads', request.user.username, today, file_obj.name)
            file_url = settings.MEDIA_URL + relative_path
            
            # 返回上传成功的响应
            return JsonResponse({
                'location': file_url
            })
            
    # 上传失败
    return JsonResponse({'error': '文件上传失败'}, status=400)


@login_required
def notebook_download_pdf(request, notebook_id):
    """下载笔记为PDF格式"""
    notebook = get_object_or_404(Notebook, id=notebook_id, user=request.user)
    
    # 生成HTML内容
    html_string = render_to_string('notebooks/notebook_pdf_template.html', {
        'notebook': notebook,
        'request': request
    })
    
    # 创建HTTP响应
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{slugify(notebook.title)}.pdf"'
    
    # 将CSS链接转换为绝对路径，确保在PDF中能正确加载样式
    base_url = request.build_absolute_uri('/')[:-1]  # 移除末尾的斜杠
    
    # 创建PDF
    buffer = BytesIO()
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
    notebook = get_object_or_404(Notebook, id=notebook_id, user=request.user)
    
    # 生成HTML内容
    html_string = render_to_string('notebooks/notebook_html_template.html', {
        'notebook': notebook
    })
    
    # 创建HTTP响应
    response = HttpResponse(content_type='text/html')
    response['Content-Disposition'] = f'attachment; filename="{slugify(notebook.title)}.html"'
    response.write(html_string)
    
    return response

