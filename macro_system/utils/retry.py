"""
重试工具模块
"""
import logging
import time
from functools import wraps
from typing import Callable, Any

logger = logging.getLogger(__name__)

def retry(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            current_delay = delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"重试{max_retries}次后失败：{e}")
                        raise
                    logger.warning(f"尝试 {attempt + 1}/{max_retries} 失败：{e}, {current_delay}s 后重试")
                    time.sleep(current_delay)
                    current_delay *= backoff
            return None
        return wrapper
    return decorator
