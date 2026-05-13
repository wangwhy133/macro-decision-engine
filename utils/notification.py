"""
通知推送模块
支持飞书 (Feishu) 和 Telegram
"""
import os
import json
import requests
from typing import Dict, Any, Optional
from macro_system.utils.logger import get_logger

logger = get_logger("macro_system.notification")

class NotificationAdapter:
    """通知适配器基类"""
    def send(self, title: str, content: str) -> bool:
        raise NotImplementedError

class FeishuAdapter(NotificationAdapter):
    """飞书机器人适配器"""
    def __init__(self, webhook: str):
        self.webhook = webhook
    
    def send(self, title: str, content: str) -> bool:
        if not self.webhook:
            return False
        
        payload = {
            "msg_type": "text",
            "content": {"text": f"**{title}**\n{content}"}
        }
        
        try:
            resp = requests.post(self.webhook, json=payload, timeout=5)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"飞书推送失败：{e}")
            return False

class TelegramAdapter(NotificationAdapter):
    """Telegram Bot 适配器"""
    def __init__(self, token: str, chat_id: str):
        self.token = token
        self.chat_id = chat_id
        self.url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    def send(self, title: str, content: str) -> bool:
        if not self.token or not self.chat_id:
            return False
        
        payload = {
            "chat_id": self.chat_id,
            "text": f"*{title}*\n{content}",
            "parse_mode": "Markdown"
        }
        
        try:
            resp = requests.post(self.url, json=payload, timeout=5)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Telegram 推送失败：{e}")
            return False

def send_notification(title: str, content: str) -> bool:
    """
    统一发送接口
    从环境变量读取配置
    """
    success = False
    
    # 1. 飞书
    feishu_webhook = os.getenv("FEISHU_WEBHOOK")
    if feishu_webhook:
        adapter = FeishuAdapter(feishu_webhook)
        if adapter.send(title, content):
            logger.info("飞书推送成功")
            success = True
        else:
            logger.warning("飞书推送失败")
    
    # 2. Telegram
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if tg_token and tg_chat_id:
        adapter = TelegramAdapter(tg_token, tg_chat_id)
        if adapter.send(title, content):
            logger.info("Telegram 推送成功")
            success = True
        else:
            logger.warning("Telegram 推送失败")
    
    if not success and not (feishu_webhook or (tg_token and tg_chat_id)):
        logger.info("未配置通知渠道，跳过推送")
    
    return success

if __name__ == "__main__":
    # 测试
    send_notification("🚀 Macro System 测试", "这是一条测试消息。")
