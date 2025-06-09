/**
 * TinyMCE 媒体文件上传处理
 * 支持图片、视频和音频文件的上传与插入
 */

// 媒体文件上传处理函数
function handleMediaUpload(callback, value, meta) {
    const input = document.createElement('input');
    input.setAttribute('type', 'file');
    
    // 根据文件类型设置接受的格式
    if (meta.filetype === 'image') {
        input.setAttribute('accept', 'image/*');
    } else if (meta.filetype === 'media') {
        input.setAttribute('accept', 'video/*,audio/*');
    } else {
        input.setAttribute('accept', 'image/*,video/*,audio/*');
    }
    
    input.onchange = function() {
        const file = this.files[0];
        if (!file) return;
        
        // 显示上传进度
        showUploadProgress();
        
        const formData = new FormData();
        formData.append('file', file);
        
        // 获取 CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        
        fetch('/notebooks/upload/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            hideUploadProgress();
            
            if (data.location) {
                // 根据文件类型插入不同的 HTML
                if (data.file_type === 'video') {
                    insertVideoElement(data.location, file.name, callback);
                } else if (data.file_type === 'audio') {
                    insertAudioElement(data.location, file.name, callback);
                } else {
                    // 图片文件
                    callback(data.location, {
                        title: file.name,
                        alt: file.name
                    });
                }
            } else {
                showError('上传失败：' + (data.error || '未知错误'));
            }
        })
        .catch(error => {
            hideUploadProgress();
            console.error('上传错误:', error);
            showError('上传失败，请重试');
        });
    };
    
    input.click();
}

// 插入视频元素
function insertVideoElement(url, filename, callback) {
    const videoHtml = `
        <div class="media-container">
            <video controls style="max-width: 100%; height: auto;">
                <source src="${url}" type="video/mp4">
                <source src="${url}" type="video/webm">
                <source src="${url}" type="video/ogg">
                您的浏览器不支持视频播放。
            </video>
            <div class="file-info">视频文件: ${filename}</div>
        </div>
    `;
    
    // 使用 TinyMCE 的 insertContent 方法插入 HTML
    if (window.tinymce && window.tinymce.activeEditor) {
        window.tinymce.activeEditor.insertContent(videoHtml);
    }
    
    // 调用回调函数（虽然我们已经插入了内容，但保持兼容性）
    callback('', {title: filename});
}

// 插入音频元素
function insertAudioElement(url, filename, callback) {
    const audioHtml = `
        <div class="media-container">
            <audio controls style="width: 100%; max-width: 500px;">
                <source src="${url}" type="audio/mpeg">
                <source src="${url}" type="audio/ogg">
                <source src="${url}" type="audio/wav">
                您的浏览器不支持音频播放。
            </audio>
            <div class="file-info">音频文件: ${filename}</div>
        </div>
    `;
    
    // 使用 TinyMCE 的 insertContent 方法插入 HTML
    if (window.tinymce && window.tinymce.activeEditor) {
        window.tinymce.activeEditor.insertContent(audioHtml);
    }
    
    // 调用回调函数
    callback('', {title: filename});
}

// 显示上传进度
function showUploadProgress() {
    // 创建进度提示元素
    const progressDiv = document.createElement('div');
    progressDiv.id = 'upload-progress';
    progressDiv.innerHTML = `
        <div style="position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); 
                    background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); 
                    z-index: 10000; text-align: center;">
            <div class="media-loading"></div>
            <span>正在上传文件...</span>
        </div>
        <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; 
                    background: rgba(0,0,0,0.5); z-index: 9999;"></div>
    `;
    document.body.appendChild(progressDiv);
}

// 隐藏上传进度
function hideUploadProgress() {
    const progressDiv = document.getElementById('upload-progress');
    if (progressDiv) {
        progressDiv.remove();
    }
}

// 显示错误信息
function showError(message) {
    // 创建错误提示
    const errorDiv = document.createElement('div');
    errorDiv.innerHTML = `
        <div style="position: fixed; top: 20px; right: 20px; background: #f8d7da; 
                    color: #721c24; padding: 15px; border-radius: 4px; border: 1px solid #f5c6cb;
                    z-index: 10000; max-width: 300px;">
            ${message}
            <button onclick="this.parentElement.remove()" style="float: right; background: none; 
                    border: none; font-size: 18px; cursor: pointer;">&times;</button>
        </div>
    `;
    document.body.appendChild(errorDiv);
    
    // 3秒后自动移除
    setTimeout(() => {
        if (errorDiv.parentElement) {
            errorDiv.remove();
        }
    }, 3000);
}

// 验证文件类型和大小
function validateFile(file) {
    const allowedImageTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/bmp', 'image/webp'];
    const allowedVideoTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/wmv', 'video/flv', 'video/webm', 'video/mkv'];
    const allowedAudioTypes = ['audio/mp3', 'audio/wav', 'audio/ogg', 'audio/aac', 'audio/flac', 'audio/m4a'];
    
    const allAllowedTypes = [...allowedImageTypes, ...allowedVideoTypes, ...allowedAudioTypes];
    
    // 检查文件类型
    if (!allAllowedTypes.includes(file.type)) {
        return {
            valid: false,
            error: '不支持的文件类型'
        };
    }
    
    // 检查文件大小
    let maxSize = 10 * 1024 * 1024; // 默认10MB
    if (allowedVideoTypes.includes(file.type)) {
        maxSize = 100 * 1024 * 1024; // 视频100MB
    } else if (allowedAudioTypes.includes(file.type)) {
        maxSize = 50 * 1024 * 1024; // 音频50MB
    }
    
    if (file.size > maxSize) {
        const sizeMB = maxSize / (1024 * 1024);
        return {
            valid: false,
            error: `文件大小超过限制（最大 ${sizeMB}MB）`
        };
    }
    
    return { valid: true };
}

// 初始化媒体拖拽上传功能
function initMediaDragUpload() {
    document.addEventListener('DOMContentLoaded', function() {
        // 为 TinyMCE 编辑器添加拖拽上传支持
        const editorContainer = document.querySelector('.tox-edit-area');
        if (editorContainer) {
            editorContainer.addEventListener('dragover', function(e) {
                e.preventDefault();
                e.stopPropagation();
                this.style.backgroundColor = '#f0f8ff';
            });
            
            editorContainer.addEventListener('dragleave', function(e) {
                e.preventDefault();
                e.stopPropagation();
                this.style.backgroundColor = '';
            });
            
            editorContainer.addEventListener('drop', function(e) {
                e.preventDefault();
                e.stopPropagation();
                this.style.backgroundColor = '';
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    handleDroppedFiles(files);
                }
            });
        }
    });
}

// 处理拖拽上传的文件
function handleDroppedFiles(files) {
    Array.from(files).forEach(file => {
        const validation = validateFile(file);
        if (!validation.valid) {
            showError(validation.error);
            return;
        }
        
        // 模拟文件选择器的回调
        handleMediaUpload(function(url, info) {
            // 文件已经通过 insertContent 插入，这里不需要额外操作
        }, '', { filetype: 'media' });
    });
}

// 初始化
initMediaDragUpload(); 