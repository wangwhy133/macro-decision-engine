"""
MDE 链路追踪 (TraceID)
贯穿数据获取 -> 策略计算 -> 下单 -> 成交 全链路
"""

import uuid
import threading
from typing import Optional, Dict, Any

# 线程本地存储
local_ctx = threading.local()

def generate_trace_id() -> str:
    """生成追踪 ID"""
    return str(uuid.uuid4())[:8]

def get_trace_id() -> Optional[str]:
    """获取当前上下文的 TraceID"""
    return getattr(local_ctx, 'trace_id', None)

def set_trace_id(trace_id: str):
    """设置当前上下文的 TraceID"""
    local_ctx.trace_id = trace_id

def clear_trace_id():
    """清除当前上下文"""
    if hasattr(local_ctx, 'trace_id'):
        del local_ctx.trace_id

class TraceContext:
    """追踪上下文管理器"""
    
    def __init__(self, trace_id: Optional[str] = None):
        self.trace_id = trace_id or generate_trace_id()
        self.metadata: Dict[str, Any] = {}
    
    def __enter__(self):
        set_trace_id(self.trace_id)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        clear_trace_id()
    
    def set(self, key: str, value: Any):
        self.metadata[key] = value
    
    def get(self, key: str) -> Any:
        return self.metadata.get(key)

# 示例用法
# with TraceContext() as ctx:
#     ctx.set('strategy', 'pig_cycle')
#     logger.info(f"[{get_trace_id()}] 开始执行策略")
#     # ... 后续所有日志自动携带 trace_id

__all__ = [
    'generate_trace_id', 'get_trace_id', 'set_trace_id', 'clear_trace_id',
    'TraceContext'
]
