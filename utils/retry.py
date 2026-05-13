"""
重试机制装饰器
用于网络请求等不稳定操作
"""
import time
import random
from functools import wraps
from typing import Callable, Any, Tuple, Type

def retry(
    retries: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    重试装饰器
    
    Args:
        retries: 最大重试次数
        delay: 初始延迟（秒）
        backoff: 延迟倍增系数
        exceptions: 触发重试的异常类型
    
    Returns:
        装饰后的函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            _retries = retries
            _current_delay = delay
            
            while _retries > 0:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    _retries -= 1
                    if _retries == 0:
                        raise  # 最后一次重试失败，抛出异常
                    
                    # 指数退避 + 抖动
                    sleep_time = _current_delay + random.uniform(0, 0.5)
                    print(f"[Retry] {func.__name__} 失败：{e}. {_retries} 次重试后 {sleep_time:.2f}s 后重试...")
                    time.sleep(sleep_time)
                    _current_delay *= backoff
            
            return None  # 理论上不会到这里
        return wrapper
    return decorator

# 快捷方式：网络请求重试
def network_retry(func: Callable) -> Callable:
    """网络请求专用重试 (3 次，指数退避)"""
    return retry(retries=3, delay=1.0, backoff=2.0, exceptions=(ConnectionError, TimeoutError))(func)
