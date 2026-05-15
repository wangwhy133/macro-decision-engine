"""
MDE 指标收集器
"""

import time
from typing import Dict, List, Optional
from collections import deque
from dataclasses import dataclass

@dataclass
class MetricPoint:
    timestamp: float
    value: float

class MetricCollector:
    """指标收集器"""
    
    def __init__(self, max_points: int = 1000):
        self.max_points = max_points
        self._metrics: Dict[str, deque] = {}
    
    def record(self, name: str, value: float):
        if name not in self._metrics:
            self._metrics[name] = deque(maxlen=self.max_points)
        self._metrics[name].append(MetricPoint(timestamp=time.time(), value=value))
    
    def get_latest(self, name: str, count: int = 1) -> List[MetricPoint]:
        if name not in self._metrics:
            return []
        return list(self._metrics[name])[-count:]
    
    def get_average(self, name: str, window_seconds: int = 60) -> Optional[float]:
        if name not in self._metrics:
            return None
        now = time.time()
        values = [p.value for p in self._metrics[name] if now - p.timestamp <= window_seconds]
        return sum(values) / len(values) if values else None
    
    def get_all_metrics(self) -> Dict[str, float]:
        return {name: points[-1].value for name, points in self._metrics.items() if points}

metrics = MetricCollector()

def record_latency(operation: str, latency_ms: float):
    metrics.record(f"latency.{operation}", latency_ms)

def record_system(metric: str, value: float):
    metrics.record(f"system.{metric}", value)

__all__ = ['MetricCollector', 'metrics', 'record_latency', 'record_system']
