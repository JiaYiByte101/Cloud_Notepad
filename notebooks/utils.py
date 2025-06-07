import requests
import json


def get_access_token():
    """
    使用应用API Key，应用Secret Key 获取access_token
    使用与accounts应用相同的百度文心一言API密钥
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
                "content": f"请帮我润色以下文本，使其更加流畅、专业。保持原意不变，只改善语言表达。直接返回润色后的文本，不要有任何额外的说明。\n\n文本：{text}"
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