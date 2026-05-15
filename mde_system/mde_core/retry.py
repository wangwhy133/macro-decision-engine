"""
MDE 重试与熔断机制
处理网络抖动和临时故障
"""

import time
import functools
from typing import Callable, Any, Optional
from datetime import datetime, timedelta

class RetryConfig:
    """重试配置"""
    def __init__(self, 
                 max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 exponential: bool = True):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential = exponential

class CircuitBreaker:
    """熔断器"""
    
    def __init__(self, failure_threshold: int = 5, recovery_time: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_time = recovery_time
        self.failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def record_success(self):
        self.failures = 0
        self.state = 'CLOSED'
    
    def record_failure(self):
        self.failures += 1
        self.last_failure_time = datetime.now()
        if self.failures >= self.failure_threshold:
            self.state = 'OPEN'
    
    def can_execute(self) -> bool:
        if self.state == 'CLOSED':
            return True
        if self.state == 'OPEN' and self.last_failure_time:
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_time):
                self.state = 'HALF_OPEN'
                return True
        return False

def retry_with_config(config: RetryConfig):
    """重试装饰器"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(config.max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt == config.max_retries:
                        break
                    
                    # 计算延迟时间
                    if config.exponential:
                        delay = min(config.base_delay * (2 ** attempt), config.max_delay)
                    else:
                        delay = config.base_delay
                    
                    print(f"执行失败，{delay:.1f}秒后重试 ({attempt+1}/{config.max_retries})")
                    time.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator

__all__ = ['RetryConfig', 'CircuitBreaker', 'retry_with_config']
