import random
import string
from django.core.cache import cache
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont
import io
import base64
import os

def generate_captcha():
    # 生成包含数字和字母的验证码
    characters = string.ascii_uppercase + string.digits
    captcha = ''.join(random.choice(characters) for _ in range(5))
    # 将验证码存入缓存，设置5分钟过期
    cache.set(f'captcha_{captcha.lower()}', captcha, 300)
    return captcha

def verify_captcha(user_input, captcha):
    # 验证码不区分大小写
    return user_input.lower() == captcha.lower()

def get_system_font():
    """获取系统字体，优先使用系统默认字体"""
    # 常见字体列表
    font_names = [
        # Windows 字体
        "C:\\Windows\\Fonts\\arial.ttf",
        "C:\\Windows\\Fonts\\simhei.ttf",
        # macOS 字体
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        # Linux 字体
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        # 通用字体
        "Arial.ttf",
        "Helvetica.ttf",
    ]
    
    # 尝试加载字体
    for font_path in font_names:
        try:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, 32)  # 增加字体大小到32
        except Exception:
            continue
    
    # 如果都失败了，返回默认字体
    return ImageFont.load_default()

def generate_captcha_image(captcha):
    # 创建图片
    width, height = 150, 50  # 增加图片尺寸
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    # 添加干扰线
    for _ in range(5):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        draw.line([(x1, y1), (x2, y2)], fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    
    # 添加干扰点
    for _ in range(100):
        x = random.randint(0, width)
        y = random.randint(0, height)
        draw.point((x, y), fill=(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)))
    
    # 获取字体
    font = get_system_font()
    
    # 绘制每个字符，添加扭曲效果
    for i, char in enumerate(captcha):
        # 随机颜色
        color = (random.randint(0, 150), random.randint(0, 150), random.randint(0, 150))
        # 随机位置偏移
        x = 25 + i * 25 + random.randint(-5, 5)  # 增加字符间距
        y = 5 + random.randint(-5, 5)
        # 随机旋转角度
        angle = random.randint(-15, 15)
        # 创建字符图片
        char_image = Image.new('RGBA', (40, 40), (0, 0, 0, 0))  # 增加字符图片尺寸
        char_draw = ImageDraw.Draw(char_image)
        char_draw.text((0, 0), char, font=font, fill=color)
        # 旋转字符
        char_image = char_image.rotate(angle, expand=True)
        # 粘贴到主图片
        image.paste(char_image, (x, y), char_image)
    
    # 转换为base64
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}" 