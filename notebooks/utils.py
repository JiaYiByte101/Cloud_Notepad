import requests
import json


def get_access_token():
    """
    使用应用API Key，应用Secret Key 获取access_token
    """
    url = "https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=BoJ2OkBmLJxxFTwsOW56GUpf&client_secret=oJB9brStNnvEdSQxoljotrPgM0spl3YD"

    payload = json.dumps("")
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json().get("access_token")


def polish_text(text):
    """
    使用百度文心一言API对文本进行润色
    
    Args:
        text: 需要润色的文本
    
    Returns:
        润色后的文本
    """
    url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/ernie-speed-128k?access_token=" + get_access_token()

    payload = json.dumps({
        "messages": [
            {
                "role": "user",
                "content": f"请帮我润色以下文本，使其更加流畅、专业。保持原意不变，只改善语言表达。直接返回润色后的文本，不要有任何额外的说明！\n\n文本：{text}"
            }
        ]
    })
    
    headers = {
        'Content-Type': 'application/json'
    }

    try:
        response = requests.request("POST", url, headers=headers, data=payload, timeout=30)
        result_json = response.json()
        
        # 获取润色后的文本
        polished_text = result_json.get("result", "")
        
        # 如果返回为空或者出错，返回原文本
        if not polished_text:
            return text
            
        return polished_text
    except Exception as e:
        print(f"AI润色失败: {str(e)}")
        return text 

def configure_pdf_fonts():
    """配置PDF生成的中文字体支持"""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.lib.fonts import addMapping
    import logging
    import os
    
    logger = logging.getLogger('notebooks')
    registered_fonts = []
    
    try:
        # 使用ReportLab内置的CID字体（优先级从高到低）
        cid_fonts = ['STSong-Light', 'MSung-Light', 'HeiseiMin-W3', 'HeiseiKakuGo-W5']
        
        for font_name in cid_fonts:
            try:
                pdfmetrics.registerFont(UnicodeCIDFont(font_name))
                addMapping(font_name, 0, 0, font_name)
                addMapping(font_name, 1, 0, font_name)
                addMapping(font_name, 0, 1, font_name)
                addMapping(font_name, 1, 1, font_name)
                registered_fonts.append(font_name)
                logger.info(f"成功注册CID字体: {font_name}")
            except Exception as e:
                logger.warning(f"CID字体 {font_name} 注册失败: {e}")
        
        # 尝试注册系统中的中文字体
        font_configs = [
            ('/usr/share/fonts/truetype/wqy/wqy-microhei.ttc', 'WenQuanYi-Micro-Hei'),
            ('/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc', 'WenQuanYi-Zen-Hei'),
            ('/System/Library/Fonts/PingFang.ttc', 'PingFang-SC'), 
            ('/Windows/Fonts/msyh.ttc', 'Microsoft-YaHei'),
            ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'DejaVu-Sans'), 
        ]
        
        for font_path, font_name in font_configs:
            try:
                if os.path.exists(font_path):
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    addMapping(font_name, 0, 0, font_name)
                    addMapping(font_name, 1, 0, font_name)
                    addMapping(font_name, 0, 1, font_name)
                    addMapping(font_name, 1, 1, font_name)
                    registered_fonts.append(font_name)
                    logger.info(f"成功注册TTF字体: {font_name}")
            except Exception as e:
                logger.warning(f"TTF字体 {font_path} 注册失败: {e}")
        
        if registered_fonts:
            logger.info(f"总共注册了 {len(registered_fonts)} 个字体: {registered_fonts}")
            return True
        else:
            logger.warning("没有成功注册任何中文字体")
            return False
        
    except Exception as e:
        logger.error(f"字体配置失败: {e}")
        return False

def prepare_pdf_html(html_string):
    """为PDF生成准备HTML字符串，替换字体名称"""
    # 配置字体
    configure_pdf_fonts()
    
    # 构建字体回退列表（优先级从高到低）
    font_fallback = 'STSong-Light, WenQuanYi-Micro-Hei, WenQuanYi-Zen-Hei, MSung-Light, HeiseiMin-W3, DejaVu-Sans, Arial, sans-serif'
    
    # 替换字体名称为已注册的字体
    replacements = [
        ('font-family: "WenQuanYi Micro Hei", Arial, sans-serif', f'font-family: {font_fallback}'),
        ('font-family: "WenQuanYi Micro Hei"', f'font-family: {font_fallback}'),
        ('font-family: "WenQuanYi Zen Hei"', f'font-family: {font_fallback}'),
        ('font-family: "SimSun"', f'font-family: {font_fallback}'),
        ('font-family: "Microsoft YaHei"', f'font-family: {font_fallback}'),
        ('Arial, sans-serif', font_fallback),
        ('sans-serif', font_fallback),
    ]
    
    for old, new in replacements:
        html_string = html_string.replace(old, new)
    
    return html_string 