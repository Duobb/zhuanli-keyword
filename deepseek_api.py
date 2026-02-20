from openai import OpenAI

def analyze_with_deepseek(api_key, keywords_text, user_text):
    if not api_key:
        return "错误：请提供 DeepSeek API Key。"
    if not keywords_text:
        return "错误：没有找到专利的关键词，请先搜索并确保有关键词结果。"
    if not user_text:
        return "错误：请输入待分析的文本。"
        
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com/v1"
    )
    
    prompt = f"""
已知以下技术分支或专利相关的关键词列表：
{keywords_text}

请认真分析下方用户输入的文本，判断其内容与上述列表中的哪个（或哪些）关键词最相关，并给出详细的分析理由：
【用户文本】：
{user_text}
"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是一个专业的专利和技术术语分析助手，能够精准拆解并映射技术关键词。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"API 调用出错：{str(e)}"
