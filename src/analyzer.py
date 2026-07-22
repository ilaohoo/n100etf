import os
import json
import logging
import requests
from typing import List, Dict

logger = logging.getLogger(__name__)

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
MODEL = "deepseek-chat"

def build_prompt(news_list: List[Dict], index_change: float, index_close: float) -> str:
    """
    构造发送给 DeepSeek 的提示词，要求严格按照之前模拟的格式输出
    """
    # 格式化新闻列表，每条用编号
    news_text = ""
    for idx, item in enumerate(news_list, 1):
        news_text += f"{idx}. [{item['symbol']}] {item['title']}\n   {item['summary']}\n   ［{item['link']}］\n\n"

    prompt = f"""你是一位专业的金融分析助手。请基于以下信息，生成一份详细的纳斯达克100指数每日复盘报告。

**指数数据**：
- 收盘点位：{index_close:.2f}
- 涨跌幅：{index_change:+.2f}%

**今日前50权重股相关新闻汇总（已去重）**：
{news_text}

请严格按照以下Markdown格式输出报告，保持结构完整，内容专业，语言精炼。不要添加额外无关内容。

---
📊 **纳斯达克100 深度复盘日报**  
**日期：** {{当前日期，格式 YYYY-MM-DD (周几)}}  
**指数收盘：** {index_close:.2f}  
**涨跌幅：** **{index_change:+.2f}%**

📈 **一、 核心指数归因分析**
（撰写一段约100-150字的归因分析，结合宏观背景、美债、VIX、板块轮动等，根据新闻内容合理推导。）

🔥 **二、 前50权重股重点动态（AI 筛选最具影响力事件）**
从上述新闻中挑选出3-5条最具市场影响力的事件，分 **🔺 利好消息** 和 **🔻 利空/风险提示** 两类列出，每条附带股票代码和简要描述（不超过50字）。

🧠 **三、 AI 详细复盘 & 后市前瞻**
**1. 情绪与资金面：** （分析当前市场情绪，资金流向，风格切换等）
**2. 关键涨跌逻辑链：** （梳理今日涨跌的传导逻辑，指出异动焦点）
**3. 明日关注焦点：** （根据已知的经济日历或事件，给出明日需要重点观察的指标或公司动态）

📎 **附：今日数据快照**
- 📉 涨跌家数比： （基于新闻中涉及的个股涨跌情绪，合理给出大致比例）
- 💰 成交额变化： （如果新闻中有提及，则引用；否则可省略）
- ⏰ 数据采集窗口： 美股收盘后 4 小时内

*🤖 本日报由 DeepSeek 自动分析生成，数据源为公开 RSS 聚合，不构成投资建议。*

---
请确保输出内容完整，不要截断。日期请根据今日实际日期填写。
"""
    return prompt

def call_deepseek(prompt: str) -> str:
    """调用 DeepSeek API，返回生成的报告文本"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是金融分析专家，擅长撰写专业复盘报告。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4000,
        "stream": False
    }
    try:
        response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        content = data['choices'][0]['message']['content']
        return content.strip()
    except Exception as e:
        logger.error(f"DeepSeek API error: {e}")
        raise

def generate_report(news_list: List[Dict], index_change: float, index_close: float) -> str:
    """主入口：生成报告"""
    prompt = build_prompt(news_list, index_change, index_close)
    logger.info("Sending prompt to DeepSeek...")
    report = call_deepseek(prompt)
    logger.info("Report generated successfully.")
    return report
