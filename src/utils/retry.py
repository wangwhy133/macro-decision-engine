# src/utils/retry.py
"""
自愈重试模块 (Self-Healing Retry)

功能:
1. 指数退避重试 (Exponential Backoff)
2. 熔断器模式 (Circuit Breaker)
3. 降级策略 (Fallback)
4. 异常分类处理

使用示例:
    @retry_with_fallback(
        max_retries=3,
        fallback=lambda: generate_mock_data(),
        backoff_factor=2.0
    )
    def fetch_data():
        return api_call()
"""

import time
import random
import logging
from functools import wraps
from typing import Callable, Any, Optional, Tuple, Type
from datetime import datetime, timedelta

logger = logging.getLogger("MDE.Retry")


class CircuitBreakerError(Exception):
    """熔断器异常"""
    pass


class RetryState:
    """重试状态管理 (每个函数独立)"""
    def __init__(self):
        self.failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.is_open = False  # 熔断器打开
        self.open_until: Optional[datetime] = None


def retry_with_fallback(
    max_retries: int = 3,
    backoff_factor: float = 2.0,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    fallback: Optional[Callable] = None,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
):
    """
    带降级策略的重试装饰器
    
    Args:
        max_retries: 最大重试次数
        backoff_factor: 退避因子 (2.0 = 指数退避)
        initial_delay: 初始延迟 (秒)
        max_delay: 最大延迟 (秒)
        jitter: 是否添加随机抖动 (防惊群)
        fallback: 降级函数 (所有重试失败后调用)
        exceptions: 需要重试的异常类型
    """
    state = RetryState()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 检查熔断器
            if state.is_open:
                if state.open_until and datetime.now() > state.open_until:
                    # 尝试恢复 (半开状态)
                    logger.info(f"熔断器半开，尝试恢复：{func.__name__}")
                    state.is_open = False
                else:
                    wait_time = (state.open_until - datetime.now()).total_seconds() if state.open_until else 0
                    raise CircuitBreakerError(
                        f"熔断器打开中，请在 {wait_time:.1f}秒后重试"
                    )
            
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    # 执行函数
                    return func(*args, **kwargs)
                
                except exceptions as e:
                    last_exception = e
                    state.failures += 1
                    state.last_failure_time = datetime.now()
                    
                    # 计算延迟
                    delay = min(initial_delay * (backoff_factor ** attempt), max_delay)
                    if jitter:
                        delay *= (0.5 + random.random() * 0.5)  # 0.5x - 1.0x
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} 失败 (尝试 {attempt+1}/{max_retries}): {e}. "
                            f"{delay:.1f}秒后重试..."
                        )
                        time.sleep(delay)
                    else:
                        # 所有重试失败
                        logger.error(f"{func.__name__} 所有重试失败: {e}")
                        
                        # 触发熔断
                        if state.failures >= max_retries * 2:  # 连续失败多次
                            state.is_open = True
                            state.open_until = datetime.now() + timedelta(minutes=5)
                            logger.error(f"熔断器打开：{func.__name__}, 5 分钟后可恢复")
                        
                        # 调用降级函数
                        if fallback:
                            logger.info(f"执行降级策略：{func.__name__}")
                            try:
                                return fallback()
                            except Exception as fallback_e:
                                logger.error(f"降级策略失败：{fallback_e}")
                        
                        # 抛出异常
                        raise last_exception from e
                
                except Exception as e:
                    # 非指定异常，直接抛出
                    logger.error(f"{func.__name__} 发生未预期异常：{e}")
                    raise
            
            # 理论上不会到这里
            raise last_exception
        
        return wrapper
    return decorator


# 便捷函数：带重试的 API 调用
def retry_api_call(func: Callable, *args, max_retries=3, fallback=None, **kwargs) -> Any:
    """同步调用带重试的函数"""
    decorated = retry_with_fallback(
        max_retries=max_retries,
        fallback=fallback
    )(func)
    return decorated(*args, **kwargs)


if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    
    # 测试 1: 成功情况
    @retry_with_fallback(max_retries=3)
    def success_func():
        return "成功"
    
    print(f"测试 1: {success_func()}")
    
    # 测试 2: 失败后重试成功 (使用闭包)
    class Counter:
        count = 0
    
    @retry_with_fallback(max_retries=3)
    def fail_then_succeed():
        Counter.count += 1
        if Counter.count < 3:
            raise ValueError("模拟失败")
        return "重试成功"
    
    print(f"测试 2: {fail_then_succeed()}")
    
    # 测试 3: 降级策略
    def mock_data():
        return {"data": "模拟数据"}
    
    @retry_with_fallback(max_retries=2, fallback=mock_data)
    def always_fail():
        raise ConnectionError("网络错误")
    
    print(f"测试 3 (降级): {always_fail()}")
    
    print("所有测试完成")
