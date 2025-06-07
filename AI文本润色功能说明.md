# AI文本润色功能说明

## 功能概述

为云记事本的TinyMCE富文本编辑器新增了AI文本润色功能。用户可以选中任意文本，点击工具栏的"AI润色"按钮，系统会调用百度文心一言API对文本进行智能润色，提升文本的流畅性和专业性。

## 功能特点

### 1. 一键润色
- **位置**: TinyMCE编辑器工具栏
- **按钮**: "AI润色"按钮，位于媒体上传按钮旁边
- **快捷操作**: 选中文本后点击即可

### 2. 实时预览
- **对比显示**: 同时显示原文和润色后的文本
- **可编辑**: 润色结果支持二次编辑
- **灵活应用**: 用户可选择是否应用润色结果

### 3. 智能处理
- **保持原意**: AI润色只改善语言表达，不改变文本含义
- **专业润色**: 提升文本的流畅性、准确性和专业性
- **错误处理**: 完善的错误提示和异常处理

## 技术实现

### 后端实现

#### 1. AI润色函数 (`notebooks/utils.py`)
```python
def polish_text(text):
    """使用百度文心一言API对文本进行润色"""
    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie-speed-128k?access_token=" + get_access_token()
    
    payload = json.dumps({
        "messages": [{
            "role": "user",
            "content": f"请帮我润色以下文本，使其更加流畅、专业。保持原意不变，只改善语言表达。直接返回润色后的文本，不要有任何额外的说明。\n\n文本：{text}"
        }]
    })
    
    response = requests.request("POST", url, headers=headers, data=payload, timeout=30)
    result_json = response.json()
    return result_json.get("result", text)
```

#### 2. 视图函数 (`notebooks/views.py`)
```python
@login_required
def ai_polish_text(request):
    """AI文本润色接口"""
    if request.method == 'POST':
        selected_text = request.POST.get('text', '').strip()
        
        if not selected_text:
            return JsonResponse({'success': False, 'error': '请先选中要润色的文本'})
        
        polished_text = polish_text(selected_text)
        
        return JsonResponse({
            'success': True,
            'polished_text': polished_text,
            'original_text': selected_text
        })
```

### 前端实现

#### TinyMCE配置更新 (`settings.py`)
1. **工具栏添加按钮**: 在toolbar配置中添加 `aiPolish`
2. **自定义按钮定义**: 在setup函数中注册AI润色按钮
3. **交互流程**:
   - 检查是否选中文本
   - 显示加载提示
   - 调用后端API
   - 显示润色结果对话框
   - 用户确认后替换原文本

## 使用流程

### 1. 选中文本
在TinyMCE编辑器中选中需要润色的文本段落

### 2. 点击润色按钮
点击工具栏中的"AI润色"按钮

### 3. 等待处理
系统显示"正在使用AI润色文本，请稍候..."的提示

### 4. 查看结果
润色完成后，弹出对话框显示：
- **原文**: 显示选中的原始文本
- **润色后**: 显示AI润色后的文本（可编辑）

### 5. 应用润色
- 点击"应用润色"：将润色后的文本替换原文本
- 点击"取消"：保持原文本不变

## 注意事项

1. **文本长度**: 建议单次润色的文本不要过长，以获得最佳效果
2. **网络连接**: 功能需要联网调用百度AI接口
3. **响应时间**: 根据文本长度和网络状况，响应时间可能在1-5秒
4. **免费额度**: 使用的是百度文心一言免费API，与账户昵称生成功能共享额度

## 错误处理

### 常见错误及解决方案

1. **未选中文本**
   - 错误提示：请先选中要润色的文本！
   - 解决方案：在编辑器中选中文本后再点击润色按钮

2. **网络错误**
   - 错误提示：AI润色失败，请稍后重试
   - 解决方案：检查网络连接，稍后重试

3. **API限制**
   - 错误提示：润色失败：API调用限制
   - 解决方案：等待一段时间后重试，或联系管理员

## 后续优化建议

1. **批量润色**: 支持对整篇文章进行分段批量润色
2. **润色风格**: 提供不同的润色风格选项（正式、轻松、学术等）
3. **历史记录**: 保存润色历史，支持撤销和重做
4. **快捷键**: 添加键盘快捷键支持
5. **离线缓存**: 缓存常见润色结果，提升响应速度

## 相关文件

- `/notebooks/utils.py` - AI润色核心函数
- `/notebooks/views.py` - 润色接口视图
- `/notebooks/urls.py` - URL路由配置
- `/cloud_notepad/settings.py` - TinyMCE配置

## 更新日志

- **2025-01-07**: 初始版本发布
  - 实现基础的AI文本润色功能
  - 集成到TinyMCE编辑器
  - 使用百度文心一言免费API