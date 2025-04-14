import random
import string
from django.core.cache import cache
from django.conf import settings
from PIL import Image, ImageDraw, ImageFont
import io
import base64

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

def generate_captcha_image(captcha):
    # 创建图片
    width, height = 120, 40
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
    
    # 添加文字
    try:
        font = ImageFont.truetype("Arial.ttf", 24)
    except IOError:
        font = ImageFont.load_default()
    
    # 绘制每个字符，添加扭曲效果
    for i, char in enumerate(captcha):
        # 随机颜色
        color = (random.randint(0, 150), random.randint(0, 150), random.randint(0, 150))
        # 随机位置偏移
        x = 20 + i * 20 + random.randint(-5, 5)
        y = 5 + random.randint(-5, 5)
        # 随机旋转角度
        angle = random.randint(-15, 15)
        # 创建字符图片
        char_image = Image.new('RGBA', (30, 30), (0, 0, 0, 0))
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