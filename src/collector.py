import feedparser
import time
from typing import List, Dict, Optional
import logging
import yaml
import requests

logger = logging.getLogger(__name__)

def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def fetch_news_for_symbol(symbol: str, rss_url_template: str, max_entries: int = 3) -> List[Dict]:
    """
    从 RSS 获取某股票的新闻，返回列表，每条包含 title, link, published, summary
    """
    url = rss_url_template.format(symbol=symbol)
    try:
        feed = feedparser.parse(url)
        entries = feed.entries[:max_entries]
        news_list = []
        for entry in entries:
            # 提取摘要（可能为 None）
            summary = entry.get('summary', '') or entry.get('description', '')
            # 去除 HTML 标签
            import re
            summary = re.sub(r'<[^>]+>', '', summary)
            news_list.append({
                'symbol': symbol,
                'title': entry.get('title', ''),
                'link': entry.get('link', ''),
                'published': entry.get('published', ''),
                'summary': summary.strip()
            })
        return news_list
    except Exception as e:
        logger.error(f"Error fetching RSS for {symbol}: {e}")
        return []

def collect_all_news() -> List[Dict]:
    """
    收集前50权重股的所有新闻，并去重（基于标题）
    返回扁平列表
    """
    config = load_config()
    tickers = config['tickers']
    rss_template = config['rss_template']
    max_news = config.get('max_news_per_ticker', 3)

    all_news = []
    for ticker in tickers:
        logger.info(f"Fetching news for {ticker}...")
        news = fetch_news_for_symbol(ticker, rss_template, max_news)
        all_news.extend(news)
        time.sleep(0.5)  # 礼貌间隔，避免被封

    # 按标题去重（保留首次出现）
    seen_titles = set()
    unique_news = []
    for item in all_news:
        if item['title'] not in seen_titles:
            seen_titles.add(item['title'])
            unique_news.append(item)
        else:
            logger.debug(f"Duplicate title skipped: {item['title']}")

    logger.info(f"Total unique news collected: {len(unique_news)}")
    return unique_news
