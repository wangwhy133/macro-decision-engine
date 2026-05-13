"""
磁盘工具模块
"""
import logging
import shutil
from typing import Dict, Any

logger = logging.getLogger(__name__)

def get_disk_usage(path: str = "/") -> Dict[str, Any]:
    """获取磁盘使用情况 (别名)"""
    return check_disk_space(path)

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

def get_db_size(db_path: str = "/opt/macro-push/data/macro.db") -> float:
    """获取数据库大小 (MB)"""
    import os
    try:
        if os.path.exists(db_path):
            return os.path.getsize(db_path) / (1024 * 1024)
        return 0.0
    except Exception as e:
        logger.error(f"获取数据库大小失败：{e}")
        return 0.0
