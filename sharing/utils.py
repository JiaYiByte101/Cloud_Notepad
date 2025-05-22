# sharing/utils.py
import re
import jieba

# 敏感词库 - 分类存储
SENSITIVE_WORDS = {
    # 侮辱性词汇
    'insult': [
        '傻子', '傻逼', '白痴', '笨蛋', '废物', '垃圾', '蠢货', 
        '混蛋', '王八蛋', '猪头', '狗屎', '畜生', '贱人',
        '废柴', '没用的东西', '蠢材', '智障', '脑残',
    ],
    
    # 粗俗词汇
    'vulgar': [
        '操', '草', '日', '艹', '尼玛', '妈的', '他妈', 
        '去死', '滚蛋', '滚开', '我靠', '靠北', '卧槽',
    ],
    
    # 歧视词汇
    'discrimination': [
        '弱智', '残废', '瘸子', '瞎子', '聋子', '二愣子',
        '外国佬', '黑鬼', '小日本', '棒子', '鬼子',
    ],
    
    # 政治敏感
    'political': [
        '文革', '六四', '反革命', '颠覆国家', '共党', '独裁',
    ]
}

# 将所有敏感词合并到一个列表中
ALL_SENSITIVE_WORDS = []
for category, words in SENSITIVE_WORDS.items():
    ALL_SENSITIVE_WORDS.extend(words)

# 常见的替代字符映射
CHAR_SUBSTITUTES = {
    '@': 'a', '4': 'a', '8': 'b', '(': 'c', '3': 'e', '6': 'g',
    '#': 'h', '!': 'i', '1': 'i', '|': 'l', '0': 'o', '$': 's',
    '7': 't', '2': 'z', '5': 's', '+': 't',
    '口': '口', '艹': '操', '西巴': '傻逼', '猪头': '笨蛋',
    '狗带': '去死', '玩意': '东西'
}

def normalize_text(text):
    """
    规范化文本，去除特殊字符、空格，替换常见的替代字符
    """
    # 转为小写
    text = text.lower()
    
    # 替换常见的替代字符
    for char, replace in CHAR_SUBSTITUTES.items():
        text = text.replace(char, replace)
    
    # 去除空格和一些特殊字符
    text = re.sub(r'\s+', '', text)
    text = re.sub(r'[,.?!;:\-_*+=~`\'"\\/<>()]', '', text)
    
    return text

def check_sensitive_words(content):
    """
    检查内容中是否包含敏感词
    返回值：如果包含敏感词，返回 (True, 检测到的敏感词); 否则返回 (False, None)
    """
    if not content or len(content.strip()) == 0:
        return False, None
    
    # 规范化文本
    normalized_content = normalize_text(content)
    
    # 直接匹配
    for word in ALL_SENSITIVE_WORDS:
        if word in normalized_content:
            return True, word
    
    # 使用jieba分词进行更精确的匹配
    try:
        words = jieba.lcut(normalized_content)
        for word in words:
            if word in ALL_SENSITIVE_WORDS:
                return True, word
                
        # 检查词组（相邻词的组合）
        for i in range(len(words) - 1):
            word_pair = words[i] + words[i+1]
            for sensitive in ALL_SENSITIVE_WORDS:
                if sensitive in word_pair:
                    return True, sensitive
    except:
        # 如果jieba未安装或出错，则忽略分词检查
        pass
    
    # 正则模式匹配常见变形（例如中间插入特殊字符）
    for word in ALL_SENSITIVE_WORDS:
        if len(word) >= 2:  # 至少2个字符的敏感词才检查变形
            # 构建一个正则表达式，允许敏感词中间插入任意字符
            pattern = ''.join([c + r'[\s\W_]*' for c in word[:-1]]) + word[-1]
            if re.search(pattern, normalized_content):
                return True, word
    
    return False, None

def get_sensitive_word_category(word):
    """
    获取敏感词所属的类别
    """
    for category, words in SENSITIVE_WORDS.items():
        if word in words:
            return category
    return None 