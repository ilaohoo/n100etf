import os
import sys
import logging
import time
from datetime import datetime
import yfinance as yf
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
    """
    获取纳斯达克100指数（优先 ^NDX，备选 QQQ）的收盘价和涨跌幅。
    自动重试最多3次，并处理周末/假日导致的数据不足问题。
    """
    symbols = ["^NDX", "QQQ"]
    for symbol in symbols:
        for attempt in range(3):
            try:
                data = yf.download(symbol, period="5d", progress=False, threads=False)
                if data.empty:
                    raise ValueError(f"No data returned for {symbol}")
                
                close_prices = data['Close'].dropna()
                if len(close_prices) < 2:
                    raise ValueError(f"Less than 2 close prices for {symbol}")
                
                today_close = close_prices.iloc[-1]
                yesterday_close = close_prices.iloc[-2]
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
        
        # 1. 获取指数数据
        index_change, index_close = get_index_data()
        
        # 2. 收集新闻
        news_list = collect_all_news()
        if not news_list:
            logger.warning("No news collected, but continuing with empty list.")
        
        # 3. 生成 AI 报告
        report = generate_report(news_list, index_change, index_close)
        
        # 4. 推送
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
