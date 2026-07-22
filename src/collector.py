import requests
import feedparser
import time
import re
import logging
from typing import List, Dict
import yaml

logger = logging.getLogger(__name__)

def load_config():
    with open("config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def fetch_news_for_symbol(symbol: str, rss_url_template: str, max_entries: int = 3) -> List[Dict]:
    """
    使用 requests + feedparser 抓取 RSS，带 User-Agent 头
    """
    url = rss_url_template.format(symbol=symbol)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"RSS request failed for {symbol}: HTTP {resp.status_code}")
            return []
        feed = feedparser.parse(resp.content)
        entries = feed.entries[:max_entries]
        news_list = []
        for entry in entries:
            summary = entry.get('summary', '') or entry.get('description', '')
            summary = re.sub(r'<[^>]+>', '', summary).strip()
            news_list.append({
                'symbol': symbol,
                'title': entry.get('title', ''),
                'link': entry.get('link', ''),
                'published': entry.get('published', ''),
                'summary': summary
            })
        return news_list
    except Exception as e:
        logger.error(f"Error fetching RSS for {symbol}: {e}")
        return []

def collect_all_news() -> List[Dict]:
    """
    收集前50权重股的新闻，如果 Google News 失败，自动切换至 RSSHub 备用源
    """
    config = load_config()
    tickers = config['tickers']
    rss_template = config['rss_template']
    max_news = config.get('max_news_per_ticker', 3)
    
    # 定义备用 RSS 模板（RSSHub 的 finance.quote 路由）
    fallback_template = "https://rsshub.app/finance/quote/{symbol}/news"
    
    all_news = []
    for ticker in tickers:
        logger.info(f"Fetching news for {ticker}...")
        news = fetch_news_for_symbol(ticker, rss_template, max_news)
        if not news:
            # 如果主源失败，尝试备用源
            logger.info(f"Primary RSS failed for {ticker}, trying fallback...")
            news = fetch_news_for_symbol(ticker, fallback_template, max_news)
        all_news.extend(news)
        time.sleep(1)  # 增加间隔，防止限流
    
    # 按标题去重
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
