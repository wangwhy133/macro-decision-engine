"""
MDE 异步并发支持
将阻塞操作放入线程池/进程池
"""

import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Callable, Any, Optional

# 全局线程池 (IO 密集型)
io_executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="mde_io")
# 全局进程池 (CPU 密集型，可选)
# cpu_executor = ProcessPoolExecutor(max_workers=4)

def run_in_thread(func: Callable, *args, **kwargs) -> asyncio.Future:
    """在线程池中运行函数"""
    loop = asyncio.get_event_loop()
    return loop.run_in_executor(io_executor, functools.partial(func, *args, **kwargs))

def async_wrap(func: Callable) -> Callable:
    """将同步函数包装为异步函数"""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        return await run_in_thread(func, *args, **kwargs)
    return wrapper

# 示例：异步获取新闻
# async_news = async_wrap(fusion_engine.get_news)
# news = await async_news(symbol='000629.SZ')

__all__ = ['io_executor', 'run_in_thread', 'async_wrap']
