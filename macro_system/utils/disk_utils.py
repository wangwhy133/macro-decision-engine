"""
磁盘工具模块
"""
import logging
import shutil
from typing import Dict, Any

logger = logging.getLogger(__name__)

def check_disk_space(path: str = "/") -> Dict[str, Any]:
    """检查磁盘空间"""
    try:
        total, used, free = shutil.disk_usage(path)
        return {
            "total": total,
            "used": used,
            "free": free,
            "percent": (used / total) * 100
        }
    except Exception as e:
        logger.error(f"磁盘检查失败：{e}")
        return {"total": 0, "used": 0, "free": 0, "percent": 0}
