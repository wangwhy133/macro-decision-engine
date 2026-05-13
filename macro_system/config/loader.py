"""
配置加载器
"""
import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

def load_config(config_path: str = None) -> Dict[str, Any]:
    """
    加载配置
    
    Args:
        config_path: 配置文件路径 (可选)
    
    Returns:
        配置字典
    """
    # 加载环境变量
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger.info(f"已加载环境变量：{env_path}")
    else:
        logger.info("使用系统环境变量")
    
    # 构建配置对象
    config = {
        "akshare_enabled": os.getenv("AKSHARE_ENABLED", "true").lower() == "true",
        "fred_api_key": os.getenv("FRED_API_KEY", ""),
        "zhipu_api_key": os.getenv("ZHIPU_API_KEY", ""),
        "ai_model": os.getenv("AI_MODEL", "glm-4"),
        "log_level": os.getenv("LOG_LEVEL", "INFO"),
        "cache_ttl_hours": int(os.getenv("CACHE_TTL_HOURS", "24")),
        "data_timeout_seconds": int(os.getenv("DATA_TIMEOUT_SECONDS", "30")),
        "anomaly_detection_enabled": os.getenv("ANOMALY_DETECTION_ENABLED", "true").lower() == "true",
        "anomaly_threshold": float(os.getenv("ANOMALY_THRESHOLD", "0.15")),
        "telegram_bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "telegram_chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
        "feishu_webhook": os.getenv("FEISHU_WEBHOOK", ""),
        "dashboard_port": int(os.getenv("DASHBOARD_PORT", "8501")),
        "dashboard_server_address": os.getenv("DASHBOARD_SERVER_ADDRESS", "0.0.0.0"),
    }
    
    logger.info("配置加载完成")
    return config
