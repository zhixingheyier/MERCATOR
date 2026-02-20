import re

# 定义中文标点到英文标点的映射表（覆盖全角/半角中文标点）
chinese_to_english_punctuation = {
    '，': ',',  '。': '.',  '！': '!',  '？': '?',  '；': ';',
    '：': ':',  '“': '"',  '”': '"',  '‘': "'",  '’': "'",
    '（': '(',  '）': ')',  '【': '[',  '】': ']',  '《': '<',
    '、': ',',  '—': '-',  '…': '...', '～': '~',
    '·': '`',  '　': ' ',  '；': ';',' ':' '
}

# 方法1：使用translate进行一对一映射替换
def replace_punctuation_translate(text):
    translator = str.maketrans(chinese_to_english_punctuation)
    return text.translate(translator)

# 方法2：正则表达式覆盖Unicode范围（补充映射表未覆盖的符号）
def replace_punctuation_regex(text):
    # 匹配所有中文标点符号（包括全角符号）
    chinese_punctuation_pattern = re.compile(
        r'[\u3000-\u303f\uff00-\uffef\u2010-\u201f\u2e80-\u2eff]'
    )
    # 替换逻辑：优先查表，未匹配的替换为空或默认符号
    return chinese_punctuation_pattern.sub(
        lambda x: chinese_to_english_punctuation.get(x.group(), ''), text
    )

# 综合方法：先映射表替换，再正则兜底
def replace_punctuation_combined(text):
    translated = replace_punctuation_translate(text)
    return replace_punctuation_regex(translated)
if __name__ == '__main__':
    text = "你好，世界！"
    print(replace_punctuation_combined(text))