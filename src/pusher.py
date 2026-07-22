import os
import logging
import requests

logger = logging.getLogger(__name__)

PUSHPULUS_TOKEN = os.environ.get("PUSHPULUS_TOKEN")
PUSHPULUS_URL = "https://www.pushplus.plus/api/send"

def send_to_pushplus(title: str, content: str, token: str = None) -> bool:
    """
    发送 Markdown 内容到 PushPlus
    """
    if token is None:
        token = PUSHPULUS_TOKEN
    if not token:
        logger.error("PUSHPULUS_TOKEN not set")
        return False

    payload = {
        "token": token,
        "title": title,
        "content": content,
        "template": "markdown"
    }
    try:
        resp = requests.post(PUSHPULUS_URL, json=payload, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        if result.get("code") == 200:
            logger.info("PushPlus send success")
            return True
        else:
            logger.error(f"PushPlus error: {result}")
            return False
    except Exception as e:
        logger.error(f"PushPlus request failed: {e}")
        return False
