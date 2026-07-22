import os
import sys
import logging
from datetime import datetime
import yfinance as yf  # 需安装 yfinance，添加到requirements
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
    """获取纳指100（QQQ）的收盘价和涨跌幅"""
    qqq = yf.Ticker("QQQ")
    hist = qqq.history(period="2d")  # 获取最近两个交易日
    if len(hist) < 2:
        raise ValueError("Not enough historical data for QQQ")
    # 最新收盘价和前一交易日收盘价
    today_close = hist['Close'].iloc[-1]
    yesterday_close = hist['Close'].iloc[-2]
    change_pct = (today_close - yesterday_close) / yesterday_close * 100
    return change_pct, today_close

def main():
    try:
        logger.info("=== Starting NASDAQ-100 daily report ===")
        
        # 1. 获取指数数据
        index_change, index_close = get_index_data()
        logger.info(f"QQQ: {index_close:.2f} ({index_change:+.2f}%)")
        
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
