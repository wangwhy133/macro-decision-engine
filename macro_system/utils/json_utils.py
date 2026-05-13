"""
JSON 工具函数
"""
import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime, date

logger = logging.getLogger(__name__)

class FlexibleEncoder(json.JSONEncoder):
    """灵活的 JSON 编码器"""
    def default(self, obj):
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        return super().default(obj)

def safe_json_dumps(obj: Any, **kwargs) -> str:
    """安全的 JSON 序列化"""
    try:
        return json.dumps(obj, cls=FlexibleEncoder, **kwargs)
    except Exception as e:
        logger.error(f"JSON 序列化失败：{e}")
        return "{}"

def safe_json_loads(s: str) -> Optional[Dict]:
    """安全的 JSON 反序列化"""
    try:
        return json.loads(s)
    except Exception as e:
        logger.error(f"JSON 反序列化失败：{e}")
        return None
