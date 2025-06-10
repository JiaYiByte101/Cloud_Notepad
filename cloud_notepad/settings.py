# cloud_notepad/settings.py

import os
from pathlib import Path
import sys
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# 加载环境变量
load_dotenv(os.path.join(BASE_DIR, ".env"))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-your-secret-key-here')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # 第三方应用
    'bootstrap4',
    'tinymce',
    
    # 项目应用
    'accounts',
    'notebooks',
    'storage',
    'sharing',
    'dashboard',
    'friends',
    'collaboration',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cloud_notepad.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# TinyMCE 配置
TINYMCE_DEFAULT_CONFIG = {
    'height': 400,
    'width': 'auto',
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 20,
    'selector': 'textarea:not([data-no-tinymce])',
    'language': 'zh_CN',
    'theme': 'silver',
    'plugins': 'advlist autolink lists link image charmap preview anchor searchreplace visualblocks code fullscreen insertdatetime media table help wordcount',
    'toolbar': 'undo redo | blocks fontselect fontsizeselect | bold italic forecolor | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | removeformat | link customMediaUpload | aiPolish | help',
    'toolbar_mode': 'sliding',
    'menubar': 'file edit view insert format tools table help',
    'statusbar': True,
    
    # 字体配置
    'font_formats': '微软雅黑=Microsoft YaHei,Helvetica Neue,PingFang SC,sans-serif;宋体=SimSun,serif;黑体=SimHei,sans-serif;楷体=KaiTi,serif;仿宋=FangSong,serif;Arial=arial,helvetica,sans-serif;Times New Roman=times new roman,times,serif;Courier New=courier new,courier,monospace',
    'fontsize_formats': '8pt 9pt 10pt 11pt 12pt 14pt 16pt 18pt 20pt 24pt 30pt 36pt 48pt 60pt 72pt 96pt',
    'image_advtab': True,
    'images_upload_url': '/notebooks/upload/',
    'automatic_uploads': True,
    'file_picker_types': 'image media file',
    'relative_urls': False,
    'remove_script_host': False,
    
    # 媒体插件配置
    'media_live_embeds': True,
    'media_filter_html': False,
    
    # 文件上传配置
    'file_picker_callback': '''function(callback, value, meta) {
        console.log('File picker called with meta:', meta);
        
        const input = document.createElement('input');
        input.setAttribute('type', 'file');
        
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
            
            const formData = new FormData();
            formData.append('file', file);
            
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
                if (data.location) {
                    if (data.file_type === 'video') {
                        const videoHtml = '<div class="media-container"><video controls style="max-width: 100%; height: auto;"><source src="' + data.location + '" type="' + (data.mime_type || 'video/mp4') + '">您的浏览器不支持视频播放。</video><div class="file-info">视频文件: ' + file.name + '</div></div>';
                        tinymce.activeEditor.insertContent(videoHtml);
                        callback('', {title: file.name});
                    } else if (data.file_type === 'audio') {
                        const audioHtml = '<div class="media-container"><audio controls style="width: 100%; max-width: 500px;"><source src="' + data.location + '" type="' + (data.mime_type || 'audio/mpeg') + '">您的浏览器不支持音频播放。</audio><div class="file-info">音频文件: ' + file.name + '</div></div>';
                        tinymce.activeEditor.insertContent(audioHtml);
                        callback('', {title: file.name});
                    } else {
                        callback(data.location, {
                            title: file.name,
                            alt: file.name
                        });
                    }
                } else {
                    alert('上传失败：' + (data.error || '未知错误'));
                }
            })
            .catch(error => {
                console.error('上传错误:', error);
                alert('上传失败，请重试');
            });
        };
        
        input.click();
    }''',
    
    # 自定义 CSS
    'content_css': [
        '/static/css/tinymce-content.css'
    ],
    
    # 有效元素配置
    'valid_elements': '*[*]',
    'extended_valid_elements': 'video[*],audio[*],source[*]',
    
    # 自定义按钮设置
    'setup': '''function(editor) {
        editor.ui.registry.addButton('customMediaUpload', {
            text: '媒体文件',
            tooltip: '上传图片、视频或音频文件',
            icon: 'upload',
            onAction: function() {
                const input = document.createElement('input');
                input.setAttribute('type', 'file');
                input.setAttribute('accept', 'image/*,video/*,audio/*');
                
                input.onchange = function() {
                    const file = this.files[0];
                    if (!file) return;
                    
                    const formData = new FormData();
                    formData.append('file', file);
                    
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
                        if (data.location) {
                            if (data.file_type === 'image') {
                                const imgHtml = '<img src="' + data.location + '" alt="' + file.name + '" style="max-width: 100%; height: auto;" />';
                                editor.insertContent(imgHtml);
                            } else if (data.file_type === 'video') {
                                const videoHtml = '<div class="media-container"><video controls style="max-width: 100%; height: auto;"><source src="' + data.location + '" type="' + (data.mime_type || 'video/mp4') + '">您的浏览器不支持视频播放。</video><div class="file-info">视频文件: ' + file.name + '</div></div>';
                                editor.insertContent(videoHtml);
                            } else if (data.file_type === 'audio') {
                                const audioHtml = '<div class="media-container"><audio controls style="width: 100%; max-width: 500px;"><source src="' + data.location + '" type="' + (data.mime_type || 'audio/mpeg') + '">您的浏览器不支持音频播放。</audio><div class="file-info">音频文件: ' + file.name + '</div></div>';
                                editor.insertContent(audioHtml);
                            }
                        } else {
                            alert('上传失败：' + (data.error || '未知错误'));
                        }
                    })
                    .catch(error => {
                        console.error('上传错误:', error);
                        alert('上传失败，请重试');
                    });
                };
                
                input.click();
            }
        });
        
        // AI润色按钮
        editor.ui.registry.addButton('aiPolish', {
            text: 'AI润色',
            tooltip: '使用AI润色选中的文本',
            icon: 'edit-block',
            onAction: function() {
                const selectedText = editor.selection.getContent({format: 'text'});
                
                if (!selectedText || selectedText.trim() === '') {
                    alert('请先选中要润色的文本！');
                    return;
                }
                
                editor.setProgressState(true);
                
                const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
                
                fetch('/notebooks/ai-polish/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                        'X-CSRFToken': csrfToken
                    },
                    body: 'text=' + encodeURIComponent(selectedText)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        editor.selection.setContent(data.polished_text);
                        editor.notificationManager.open({
                            text: 'AI润色完成！',
                            type: 'success',
                            timeout: 2000
                        });
                    } else {
                        alert('AI润色失败：' + (data.error || '未知错误'));
                    }
                })
                .catch(error => {
                    console.error('AI润色错误:', error);
                    alert('AI润色失败，请稍后重试');
                })
                .finally(() => {
                    editor.setProgressState(false);
                });
            }
        });
    }''',
}

WSGI_APPLICATION = 'cloud_notepad.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME', 'cloud_notepad'),
        'USER': os.getenv('DB_USER', 'root'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
        }
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Authentication settings
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'collaboration': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'notebooks': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'storage': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'storage.backends.cloud': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}

# === 腾讯云 COS 设置 ===
COS_REGION = "ap-nanjing"
COS_SECRET_ID = os.getenv("TENCENT_COS_SECRET_ID")
COS_SECRET_KEY = os.getenv("TENCENT_COS_SECRET_KEY")
COS_BUCKET_NAME = "cloud-notepad-1330914960"
COS_DOMAIN = "https://cloud-notepad-1330914960.cos.ap-nanjing.myqcloud.com"

# 使用 COS 作为默认文件存储系统
DEFAULT_FILE_STORAGE = 'cloud_notepad.storage_backends.TencentCOSStorage'

# Django 4.2+ 新的存储配置方式
STORAGES = {
    "default": {
        "BACKEND": "cloud_notepad.storage_backends.TencentCOSStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

print("✅ DEFAULT_FILE_STORAGE =", DEFAULT_FILE_STORAGE, file=sys.stderr)

# === 文件上传配置 ===
# 数据上传最大内存大小 (100MB)
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024

# 文件上传最大内存大小 (100MB) 
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024

# 请求体最大大小
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

# 文件上传处理器
FILE_UPLOAD_HANDLERS = [
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
]
