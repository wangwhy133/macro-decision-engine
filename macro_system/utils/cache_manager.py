"""
缓存管理模块
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def get_cache(ttl_hours: int = 24) -> Dict[str, Any]:
    """获取缓存管理器"""
    return CacheManager(ttl_hours)

class CacheManager:
    """缓存管理器"""
    
    def __init__(self, ttl_hours: int = 24):
        self.ttl = timedelta(hours=ttl_hours)
        self._cache: Dict[str, Dict[str, Any]] = {}
        logger.info(f"缓存管理器初始化，TTL={ttl_hours}小时")
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self._cache:
            entry = self._cache[key]
            if datetime.now() < entry["expires"]:
                return entry["data"]
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """设置缓存"""
        self._cache[key] = {
            "data": value,
            "expires": datetime.now() + self.ttl
        }
        logger.debug(f"缓存已设置：{key}")
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
