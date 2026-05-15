"""
MDE 数据源健康检查
- 实时监控各数据源可用性
- 自动切换备用源
- 熔断保护
"""

import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from threading import Thread

class SourceHealth:
    """数据源健康状态"""
    def __init__(self, name: str):
        self.name = name
        self.success_count = 0
        self.fail_count = 0
        self.last_success: Optional[datetime] = None
        self.last_fail: Optional[datetime] = None
        self.is_healthy = True
        self.latency_ms: float = 0.0
    
    def record_success(self, latency_ms: float):
        self.success_count += 1
        self.last_success = datetime.now()
        self.latency_ms = latency_ms
        self.is_healthy = True
        # 成功后减少失败计数
        self.fail_count = max(0, self.fail_count - 1)
    
    def record_failure(self):
        self.fail_count += 1
        self.last_fail = datetime.now()
        if self.fail_count >= 3:
            self.is_healthy = False
    
    def get_score(self) -> float:
        """健康评分 (0-1)"""
        total = self.success_count + self.fail_count + 1
        return self.success_count / total

class HealthChecker:
    """健康检查管理器"""
    
    def __init__(self, check_interval: int = 60):
        self.check_interval = check_interval
        self.sources: Dict[str, SourceHealth] = {}
        self._running = False
        self._thread: Optional[Thread] = None
    
    def register(self, name: str):
        """注册数据源"""
        if name not in self.sources:
            self.sources[name] = SourceHealth(name)
    
    def record(self, name: str, success: bool, latency_ms: float = 0.0):
        """记录请求结果"""
        if name not in self.sources:
            self.register(name)
        
        if success:
            self.sources[name].record_success(latency_ms)
        else:
            self.sources[name].record_failure()
    
    def get_healthy_sources(self) -> List[str]:
        """获取健康的数据源列表"""
        return [name for name, health in self.sources.items() if health.is_healthy]
    
    def get_best_source(self) -> Optional[str]:
        """获取最健康的数据源"""
        healthy = self.get_healthy_sources()
        if not healthy:
            return None
        
        # 选择成功率最高的
        best = max(healthy, key=lambda x: self.sources[x].get_score())
        return best
    
    def start(self):
        """启动后台检查 (可选)"""
        self._running = True
        self._thread = Thread(target=self._check_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        self._running = False
    
    def _check_loop(self):
        while self._running:
            # 这里可以添加主动探测逻辑
            time.sleep(self.check_interval)

# 全局实例
health_checker = HealthChecker()

__all__ = ['SourceHealth', 'HealthChecker', 'health_checker']
