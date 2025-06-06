# cloud_notebook/settings.py

import os
from pathlib import Path
import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'your-secret-key'  # 在生产环境中应该保密

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
    'bootstrap4',  # 或者使用 Bootstrap 5
    'tinymce',
    
    # 项目应用
    'accounts',
    'notebooks',
    'storage',
    'sharing',
    'dashboard',
    'friends',  # 好友应用
    'collaboration',  # 多人协作应用
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

TINYMCE_DEFAULT_CONFIG = {
    'height': 400,
    'width': 'auto',
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 20,
    'selector': 'textarea:not([data-no-tinymce])',  # 排除带有data-no-tinymce属性的textarea
    'language': 'zh_CN',
    'theme': 'silver',
    'plugins': 'advlist autolink lists link image charmap preview anchor searchreplace visualblocks code fullscreen insertdatetime media table help wordcount',
    'toolbar': 'undo redo | blocks | bold italic forecolor | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | removeformat | link image media customMediaUpload | help',
    'toolbar_mode': 'sliding',
    'menubar': 'file edit view insert format tools table help',
    'statusbar': True,
    'image_advtab': True,
    'images_upload_url': '/notebooks/upload/',
    'automatic_uploads': True,
    'file_picker_types': 'image media file',
    'relative_urls': False,
    'remove_script_host': False,
    
    # 媒体插件配置
    'media_live_embeds': True,
    'media_filter_html': False,
    
    # 文件上传配置 - 使用自定义的处理函数
    'file_picker_callback': '''function(callback, value, meta) {
        console.log('File picker called with meta:', meta);
        
        // 创建文件输入元素
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
            
            console.log('File selected:', file.name, file.type);
            
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
                console.log('Upload response:', data);
                if (data.location) {
                    if (data.file_type === 'video') {
                        // 插入视频元素
                        const videoHtml = '<div class="media-container"><video controls style="max-width: 100%; height: auto;"><source src="' + data.location + '" type="' + (data.mime_type || 'video/mp4') + '">您的浏览器不支持视频播放。</video><div class="file-info">视频文件: ' + file.name + '</div></div>';
                        tinymce.activeEditor.insertContent(videoHtml);
                        callback('', {title: file.name});
                    } else if (data.file_type === 'audio') {
                        // 插入音频元素
                        const audioHtml = '<div class="media-container"><audio controls style="width: 100%; max-width: 500px;"><source src="' + data.location + '" type="' + (data.mime_type || 'audio/mpeg') + '">您的浏览器不支持音频播放。</audio><div class="file-info">音频文件: ' + file.name + '</div></div>';
                        tinymce.activeEditor.insertContent(audioHtml);
                        callback('', {title: file.name});
                    } else {
                        // 图片文件
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
    
    # 有效元素配置，允许视频和音频标签
    'valid_elements': '*[*]',
    'extended_valid_elements': 'video[*],audio[*],source[*]',
    
    # 自定义按钮设置
    'setup': '''function(editor) {
        editor.ui.registry.addButton('customMediaUpload', {
            text: '视频/音频',
            tooltip: '上传视频或音频文件',
            onAction: function() {
                const input = document.createElement('input');
                input.setAttribute('type', 'file');
                input.setAttribute('accept', 'video/*,audio/*');
                
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
    }''',
}

WSGI_APPLICATION = 'cloud_notepad.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
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
LANGUAGE_CODE = 'zh-hans'  # 使用中文
TIME_ZONE = 'Asia/Shanghai'  # 使用中国时区
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
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
        },
    },
}
