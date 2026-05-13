"""
文件锁模块
"""
import logging
from functools import wraps
from typing import Callable

logger = logging.getLogger(__name__)

def db_lock(func: Callable) -> Callable:
    """数据库锁装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.debug("获取数据库锁...")
        try:
            return func(*args, **kwargs)
        finally:
            logger.debug("释放数据库锁")
    return wrapper
