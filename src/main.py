import os
import sys
import logging
import time
from datetime import datetime
import requests
from collector import collect_all_news
from analyzer import generate_report
from pusher import send_to_pushplus

# 配置日志
os.makedirs("logs", exist_ok=True)
log_filename = f"logs/report_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def get_index_data():
    symbols = ["^NDX", "QQQ"]
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }
    for symbol in symbols:
        for attempt in range(3):
            try:
                url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
                resp = requests.get(url, headers=headers, timeout=10)
                if resp.status_code != 200:
                    raise ValueError(f"HTTP {resp.status_code}")
                data = resp.json()
                result = data.get('chart', {}).get('result')
                if not result:
                    raise ValueError("No result in response")
                quote = result[0]
                close_prices = quote.get('indicators', {}).get('quote', [{}])[0].get('close', [])
                if not close_prices or len(close_prices) < 2:
                    raise ValueError("Not enough close prices")
                closes = [c for c in close_prices if c is not None]
                if len(closes) < 2:
                    raise ValueError("Less than 2 valid close prices")
                today_close = closes[-1]
                yesterday_close = closes[-2]
                change_pct = (today_close - yesterday_close) / yesterday_close * 100
                logger.info(f"Fetched {symbol}: {today_close:.2f} ({change_pct:+.2f}%)")
                return change_pct, today_close
            except Exception as e:
                logger.warning(f"Attempt {attempt+1} for {symbol} failed: {e}")
                time.sleep(2)
        logger.warning(f"All attempts failed for {symbol}, trying next symbol...")
    raise RuntimeError("Failed to fetch index data from all symbols after retries")

def main():
    try:
        logger.info("=== Starting NASDAQ-100 daily report ===")
        index_change, index_close = get_index_data()
        news_list = collect_all_news()
        if not news_list:
            logger.warning("No news collected, but continuing with empty list.")
        report = generate_report(news_list, index_change, index_close)
        title = f"纳指100复盘 {datetime.now().strftime('%Y-%m-%d')}"
        success = send_to_pushplus(title, report)
        if success:
            logger.info("Report sent successfully.")
        else:
            logger.error("Failed to send report via PushPlus.")
            sys.exit(1)
    except Exception as e:
        logger.exception("Fatal error in main workflow")
        sys.exit(1)

if __name__ == "__main__":
    main()
